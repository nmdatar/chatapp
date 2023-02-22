import pytest
import grpc
# from grpc_testing import server_from_descriptor

from proto import chatapp_pb2 as chatapp
from proto import chatapp_pb2_grpc as rpc

address = 'localhost'
port = 11912


@pytest.fixture(scope="module")
def grpc_channel():
    channel = grpc.insecure_channel(address + ':' + str(port))
    print("channel", channel)
    yield channel


@pytest.fixture(scope='module')
def grpc_stub(grpc_channel):
    print("grpc_channel", grpc_channel)
    return rpc.ChatServiceStub(grpc_channel)

# Create_Account TC1: User only creates account if username is unique


def test_create_1(grpc_stub):
    username = "user1"
    password = "p1"
    request = chatapp.Account(username=username, password=password)
    grpc_stub.CreateAccount(request)
    response = grpc_stub.CreateAccount(request)
    assert response.success == False

# Login TC1: User only logs in if account created


def test_login_1(grpc_stub):
    # Set up test data
    username = 'user2'
    password = 'p1'

    # Create login request
    request = chatapp.Account(username=username, password=password)
    # Call the gRPC login function
    response = grpc_stub.LoginAccount(request)
    # Verify the response is successful
    assert response.success == False

# Login TC2: Logs in if password is correct


def test_login_2(grpc_stub):
    # Set up test data
    username = 'user3'
    password = 'p1'
    res1 = grpc_stub.CreateAccount(chatapp.Account(
        username=username, password=password))
    if res1.success:
        res2 = grpc_stub.LoginAccount(chatapp.Account(
            username=username, password="wrongpassword"))
    assert res2.success == False

# Logout TC1: Log out successfully if valid account


def test_logout_1(grpc_stub):
    username = "user4"
    response = grpc_stub.LogoutAccount(chatapp.Account(username=username))
    assert response.success == False
    response = grpc_stub.CreateAccount(
        chatapp.Account(username=username, password="p1"))
    assert response.success == True

# Logout TC1: Log out successfully if account logged in


def test_logout_2(grpc_stub):
    username = "user4"
    response = grpc_stub.LogoutAccount(chatapp.Account(username=username))
    assert response.success == True

# List_Accounts TC1: Lists proper accounts


def test_list_account_1(grpc_stub):
    wildcard = "%"
    grpc_stub.CreateAccount(chatapp.Account(username="xy%"))
    grpc_stub.CreateAccount(chatapp.Account(username="%"))
    response = grpc_stub.ListAccounts(
        chatapp.ListAccountQuery(search_term=wildcard))
    print(response, "response")


# Send_Message TC1: Message sends to valid and logged in user


def test_send_message_1(grpc_stub):
    grpc_stub.CreateAccount(chatapp.Account(username="u1"))
    grpc_stub.CreateAccount(chatapp.Account(username="u2"))
    grpc_stub.LoginAccount(chatapp.Account(username="u1"))
    grpc_stub.LoginAccount(chatapp.Account(username="u2"))

    res1 = grpc_stub.SendMessage(chatapp.Message(
        fromUsername="u1", toUsername="u2", message="test message 1"))
    res2 = grpc_stub.SendMessage(chatapp.Message(
        fromUsername="u1", toUsername="u2", message="test message 2"))

    grpc_stub.DeleteAccount(chatapp.Account(username="u2"))

    res3 = grpc_stub.SendMessage(chatapp.Message(
        fromUsername="u2", toUsername="u1", message="test message back"))

    assert res1.success == True and res2.success == True and res3.success == False

# Send_Message TC2: Message queues if recipient not logged in


def test_send_message_2(grpc_stub):
    grpc_stub.CreateAccount(chatapp.Account(username="u1"))
    grpc_stub.CreateAccount(chatapp.Account(username="u2"))
    grpc_stub.LoginAccount(chatapp.Account(username="u1"))
    grpc_stub.LogoutAccount(chatapp.Account(username="u2"))

    res1 = grpc_stub.SendMessage(chatapp.Message(
        fromUsername="u1", toUsername="u2", message="test message 1"))
    res2 = grpc_stub.SendMessage(chatapp.Message(
        fromUsername="u1", toUsername="u2", message="test message 2"))

    assert res1.success == True and res2.success == True

# Delete_Account TC1: Deletes accounts and deletes user messages


def test_delete_account(grpc_stub):
    grpc_stub.CreateAccount(chatapp.Account(username="u1"))
    res1 = grpc_stub.CreateAccount(chatapp.Account(username="u1"))

    grpc_stub.DeleteAccount(chatapp.Account(username="u1"))
    res2 = grpc_stub.CreateAccount(chatapp.Account(username="u1"))

    assert res1.success == False and res2.success == True
