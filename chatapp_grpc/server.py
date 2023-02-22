from concurrent import futures
from typing import List

import grpc
import time

from proto import chatapp_pb2 as chatapp
from proto import chatapp_pb2_grpc as rpc


class ChatServer(rpc.ChatServiceServicer):

    def __init__(self):
        # username: list of dict
        # dict: {}
        self.usernames = {}

        # messages: list of objects
        # dict: { from: str, to: str, message: str }
        self.messages: List = []

        # messages: list of objects
        # dict: { from: str, to: str, message: str }
        self.queued_messages: List = []

        # retry message flag
        # str | None
        self.retry_flag = None

    """Function that creates new account"""

    def CreateAccount(self, request: chatapp.Account, context):
        username = request.username
        password = request.password
        print(f'creating account for username: {username}')

        # if account already exists
        if username in self.usernames:
            return chatapp.CommonResponse(success=False, message="Account Exists Already")
        # otherwise, create account and automatically log user in
        self.usernames[username] = {}
        self.usernames[username]["online"] = True
        self.usernames[username]["password"] = password
        return chatapp.CommonResponse(success=True, message="Account Created Succesfully")

    """Function to delete existing account"""

    def DeleteAccount(self, request: chatapp.User, context):
        # user can only delete account when logged in
        username = request.username
        print(f'deleting username: {username}')
        # checking account to be deleted is a valid account
        if username not in self.usernames:
            return chatapp.CommonResponse(success=False, message="Username doesn't exist")

        # deleting username
        del self.usernames[username]

        # delete messages
        for message_obj in self.messages:
            if message_obj['fromUsername'] == username:
                self.messages.remove(message_obj)

        for message_obj in self.queued_messages:
            if message_obj['fromUsername'] == username:
                self.queued_messages.remove(message_obj)

        return chatapp.CommonResponse(success=True, message="Username deleted Succesfully")

    """Function to log in valid account"""

    def LoginAccount(self, request: chatapp.Account, context):
        username = request.username
        password = request.password
        print(f'login username: {username}')
        # check if user exists and password is correct
        if username in self.usernames and self.usernames[username]["password"] == password:
            self.usernames[username]["online"] = True
            return chatapp.CommonResponse(success=True, message='Username logged in Succesfully')
        return chatapp.CommonResponse(success=False, message="Username doesn't exist")

    """Function to log out account"""

    def LogoutAccount(self, request: chatapp.User, context):
        username = request.username
        print(f'logout username: {username}')
        # check if user is valid
        if username not in self.usernames:
            return chatapp.CommonResponse(success=False, message="Username doesn't exist")
        # set user "online" to false
        self.usernames[username]["online"] = False
        return chatapp.CommonResponse(success=True, message="Username logged in Succesfully")

    """Function to list matching accounts"""

    def ListAccounts(self, request: chatapp.ListAccountQuery, context):
        search_term = request.search_term
        print(f'listing accounts with search term: {search_term}')

        if search_term is not None:
            search_term = request.search_term
            # find matching accounts
            matching_accounts = [
                username for username in self.usernames if search_term in username]

            for account in matching_accounts:
                yield chatapp.Account(username=account)
        else:
            # return all accounts
            for account in self.usernames:
                yield chatapp.Account(username=account)

    """Function to send messages recipient"""

    def SendMessage(self, request: chatapp.Message, context):
        fromUsername = request.fromUsername
        toUsername = request.toUsername
        message = request.message

        print(f'{fromUsername} send the following message to {toUsername}: {message}')
        # check if sender is valid
        if fromUsername not in self.usernames:
            return chatapp.CommonResponse(success=False, message="From username doesn't exist")
        # check if recipient is valid
        if toUsername not in self.usernames:
            return chatapp.CommonResponse(success=False, message="To username doesn't exist")

        message_obj = {
            'fromUsername': fromUsername,
            'toUsername': toUsername,
            'message': message
        }
        # add message to message list if recipient is logged in
        if (self.usernames[toUsername]["online"] == True):
            self.messages.append(message_obj)
            return chatapp.CommonResponse(success=True, message="Message Queued")
        else:
            # add messages to queue if recipient not logged in
            self.queued_messages.append(message_obj)
        return chatapp.CommonResponse(success=True, message="Message sent Succesfully")

    """Function listening to constantly send messages"""

    def ChatStream(self, request_iterator, context):
        last_index = 0

        while True:
            # retry undelivered message flag is on
            if self.retry_flag is not None:
                print("queue", self.queued_messages[:])
                for message_obj in self.queued_messages[:]:
                    # send only to online users
                    if (message_obj["toUsername"] == self.retry_flag
                            and self.usernames[message_obj["toUsername"]]["online"] == True):
                        # delete queued message in original queue
                        self.queued_messages.remove(message_obj)
                        yield chatapp.Message(fromUsername=message_obj['fromUsername'], toUsername=message_obj['toUsername'], message=message_obj['message'])

                # reset retry flag
                self.retry_flag = None

            # stream messages to online users
            while len(self.messages) > last_index:
                message_obj = self.messages[last_index]
                last_index += 1
                print(message_obj)
                yield chatapp.Message(fromUsername=message_obj['fromUsername'], toUsername=message_obj['toUsername'], message=message_obj['message'])

    """Function to deliver queued messages"""

    def DeliverMessages(self, request: chatapp.User, context):
        username = request.username
        print(f'retry message(s) to {username}')
        # send if recipient is valid and online
        if username in self.usernames and self.usernames[username]["online"] == True:
            self.retry_flag = username
            return chatapp.CommonResponse(success=True, message="Retrying messages now")
        return chatapp.CommonResponse(success=False, message="Username doesn't exist or not logged in")


if __name__ == "__main__":
    port = 11912
    # creating a server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    rpc.add_ChatServiceServicer_to_server(ChatServer(), server)

    print(f'✅ Starting server. Listening on port {port}')
    server.add_insecure_port('[::]:' + str(port))
    server.start()

    while True:
        time.sleep(64 * 64 * 100)
