import asyncio


class ControlServer(object):
    def __init__(self, robot, port=5656, loop=asyncio.get_event_loop()):
        self.robot = robot

        # Set up the socket server
        coro = asyncio.start_server(self.handle_socket, port=port)
        self.async_server = loop.run_until_complete(coro)

    # Define the queueing mechanism for commands received over the control socket
    async def handle_socket(self, reader, writer):
        writer.write(b'>> ')

        while True:
            line = await reader.readline()
            if line == b'':
                break
            command = line.decode('utf8').strip()
            self.robot.enqueue(command, writer)
            print('Queued:', command)
            writer.write(b'>> ')

    def shutdown(self):
        pass

