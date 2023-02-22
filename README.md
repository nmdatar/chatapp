# Chat App

## Get Started

#### **Pip**

First, make sure you installed Pipenv, a virtual enviroment manager.

Install all dependencies via `pipenv install`

Enter the virtual enviroment via `pipenv shell`

Depending on the project, refer to either 'gRPC' or 'WebSocket'

#### **Conda**

If you prefer working with conda and have it installed, please run the following commands:

`conda env create -f environment.yml`

​`conda activate chatapp`

Now you will be all set!

### gRPC

Run Server `python3 chatapp_grpc/server.py`

Run Client `python3 chatapp_grpc/client.py`

Install .proto file `python3 -m grpc_tools.protoc --proto_path=. ./proto/chatapp.proto --python_out=. --grpc_python_out=.`

### WebSocket

Run Server `python3 chatapp_websocket/server.py`

Run Client `python3 chatapp_websocket/client.py`

# Documentation for Design Project 1

## Part I: Server Side

The server side sets up the clients to engage in a chat application with the following functionalities (which will be elaborated on further on).

First, we have to set up the client request to be received by the server in the first place. This function, titled handle_client has two arguments (clientsocket, addr) which are the client socket name and client address respectively. We have two dictionaries set up for this. The dictionary enables the access of other account information that includes passwords, their online status, as well as their received messages. We use another dictionary entitled socket_to_user that maps a socket address to the given account name. The data will be received using the clientsocket.recv(1024) function which updates the accounts and socket_to_user dictionaries accordingly and closes if data is not present. 1024 will be the maximum amount of data (in bytes) that can be received at a time and therefore will have a buffer size of 1024 bytes

Now, we will go into each of the action-oriented functions that we have created.

Create: creates a new account with a provided username and password if the username doesn’t exist, otherwise returns error message
List: returns list of all usernames that match provided search term, otherwise returns all usernames in the dictionary
Login: logs in the user with provided username and password if username exists, not logged in, and has the correct username password match. After logged in, it checks for undelivered messages, and if there are any, delivers them to user, otherwise returns error  
Send: sends message from sender to recipient if recipient exists and logged in, if not logged in, stores the message in the received_message list, otherwise returns error
Deliver: delivers any undelivered messages with the provided username and password if they exist and are logged in, otherwise returns error
Delete: deletes the account with the provided username and password if it exists and is not currently logged in by another client. if the account has undelivered messages, the function delivers them to the user, otherwise, it returns an error message. We have done this outside the login side so that undelivered messages are still accounted for on both sides despite the user not existing anymore (i.e. if the sender’s account got deleted as well as the receiver’s one). Although if the sender’s account got deleted and the messages are queued to send (which it will still do), structuring it this way also ensures that if the receiver’s account gets deleted, the messages in the queue will still send.

If none of the above functions are recognized, then an error message will show saying that the request was not found.

To tie things up, the overall script has been set up using TCP sockets for communication and a dictionary to store account names. It listens for a specific port that we have specified to look out for incoming connections from clients (which will be elaborated in the following section). Each new TCP socket will be created using the socket.socket() function, selectors.DefaultSelector to monitor new connections, and threading.Thread to handle simultaneous requests through multithreading to allow the requests to take place in a separate thread. This was done to enable the efficient processing and capabilities of many different clients.

Part B: Client Side

On the client side, the user is allowed to send request to the server using commands in the following:

Linking to the server involves the client socket object creation using socket.socket() with parameters AF_INET and SOCK_STREAM that specifies the address family of the socket as IPv4 and the TCP type respectively. We then connect to the server using the IP address and the port number specified on the server end using clientsocket.connect() with the aforementioned as the parameters. Here, the user will be prompted with a message to enter a command using a standard print() statement.

Firstly, our program has the select module that monitors the client socket and the standard input stream for incoming data. It checks if it comes from the server or the user (using select.select()) to decide what to do. If the message is from the server, the message will be decoded and printed using the print() statement. If from the user, we will proceed with the following:

The cmap dictionary maps user command strings to integers that are sent to the server. This is done to simplify the message protocol and reduce the amount of data that needs to be transmitted. The code also includes some special handling for the "login", "delete", and "deliver" commands. When any of these commands are entered by the user, the code waits for the server to send a response with a specific ending sequence of characters ("\r\n\r\n"). This is done to ensure that all messages have been delivered before continuing with the next command.

Finally to tidy everything up, the command will be sent to the server using clientsocket.send(), display undelivered messages from the buffer to the user if command = login, deliver, or delete, and if not those three, the response is received and displayed using clientsocket.recv().

To recap the usability side of things that the user will input to the client, we will use the following format to send the aforementioned commands:

- Create username password
- Delete username password
- Deliver username message

Other features we have later integrated are the following to ensure general reliability across commands (UPDATES):

Between the client and the server, they each have a version and it first checks if the message that is coming from the client has that version; otherwise it rejects the version. In an actual protocol, a server may have commands that are present in one version that aren't in the other so we use this restriction so that all compatiibilities are met. This is something that we realized we needed to account for as we were developing our code.

Furthermore, since we can't send messages as a string, we have the encode message as a UTF-8 as a series of bytes in order for the commands to be sent across in the functions we have outlined above. We considered sending the entire string but we realized this would be sending way more data than needed.

## Part II: gRPC

### Protocol Buffers

The .proto file is where we defined our service by providing the methods that we want our service to provide. In our .proto file, we various methods (corresponding to functions required for the assignment) and set parameters for each method. For methods such as `login` and `logout` which only require a singular request and response, we set it as unary. For methods requiring multiple requests and/or responses from client/server, we set a streaming method. For example `list_accounts` requires the server to list a stream of accounts, we set it to be a server-side streaming method.

### Server

The server.py program creates a gRPC server and listens for requests from the client to respond with the according method defined in the .proto file. The server.py program also implements the service defined in the .proto file to send back appropriate responses.

### Client

The client.py program creates a gRPC channel that connects to the server on a particular port and creates a stub, which gives us the ability to make RPC calls to the server, for the service/method it wants to call (as we defined in the .proto file). The user enters information in the commandline, which instructs the client.py program to make certain requests to the gRPC server, receive responses, and display those responses.

### Create Account, Login, Logout

Since the `CreateAccount` and `Login` function have overlapping abilities, I combined the two functions into one, the `Login` function. In the server, I created a dictionary called `usernames` on the server's RAM to store every user and their connectivity. The `Login` function checks if the user is registered, if not, it creates a new user and logs them in. Otherwise, it simply logs them in. The `Logout` receives the client currently logged in and disconnects them from the server and sets their connectivity in the `usernames` dictionary. I created my Client so that each client can only access one terminal, so the logout function automatically logs out the current user without asking for username.

### List Accounts

Returns list of all usernames that match provided search term, otherwise returns all usernames in the dictionary

### Send Messages, Deliver Messages

I created a `ChatStream` in server.py which provides a bidirectional streaming RPC method between the server and client ( when client creates a thread for message streaming, this function is always called, or the server is always listening to client's requests). The function is constantly running to 1) identify if `self.retry_flag == username`, which indicates that there are queued messages to be sent (Deliver Message) or 2) if the dictionary stored new messages. In both cases, it sends messages the client by yielding a chatapp.Message object

With `ChatStream` running in the back, `SendMessage` stores message in `self.messages` if recipient is logged in (which `ChatStream` sends to recipient as we explained above), if not logged in, stores the message in the queued_messages list. `Retry` delivers the queued_message when the recipient is logged in.

### Delete Account

You delete the account if you are logged in. After you delete the account, all your messages and queued_messages (unsent messages) are deleted as well. This was designed with the intention that if an user deletes an account, maybe there are messages they don't want to see and the current application doesn't allow user to select which messages to view.

### Comparison: gRPC vs. Websocket

There are multiple differences between the performance of gRPC and Websockets because of the way gRPC is designed. First of all, gRPC is higher performing than WebSocket because it uses HTTP/2, which allows gRPC to handle multiple gRPC calls between client and servers with a few TCP connections. gRPC also uses binary encoding of protocol buffers, meaning the size of the buffers of the same information being sent back and forth is smaller than traditional text-based protocols like HTTP or WebSocket.

gRPC is also less complex than Websockets because gRPC provides high-level abstraction for defining and implementing remote procedures. As we have explained previously, the developer using gRPC only needs to define the service interface for protocol buffers in .proto and gRPC auto-generates the server and client code. On the contrary, implementing the WebSocket method requires implementing details of establishing a connection, sending and receiving messages, parsing data, etc, which makes the program more complex and therefore more prone to error.
