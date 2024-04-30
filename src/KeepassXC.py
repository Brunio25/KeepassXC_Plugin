import subprocess
import threading
import queue
import os


class KeepassXC:
    def __init__(self):
        database_path = "path"
        self.keepassxc_process = subprocess.Popen(["keepassxc-cli",
                                                  "open",
                                                  database_path],
                                                  stdin=subprocess.PIPE,
                                                  stdout=subprocess.PIPE,
                                                  stderr=subprocess.DEVNULL,
                                                  text=True)
        self.output_queue = queue.Queue()
        self.read_thread = threading.Thread(target=self.read_output)
        self.read_thread.start()
        self.__database_name = os.path.basename(database_path).split(".")[0]
        self.__write_command("password")

    def read_output(self):
        while True:
            try:
                output = self.keepassxc_process.stdout.readline()
                if output and not output.startswith(self.__database_name):
                    self.output_queue.put(output)
                elif output:
                    continue
                else:
                    break
            except ValueError:
                break

    def get_output(self):
        try:
            return self.output_queue.get(timeout=0.1)  # Non-blocking read with timeout
        except queue.Empty:
            return None

    def __write_command(self, command):
        if command == "exit":
            self.keepassxc_process.stdin.close()
            self.keepassxc_process.stdout.close()
            self.keepassxc_process.stderr.close()
            self.keepassxc_process.wait()
            return

        self.keepassxc_process.stdin.write(command + "\n")
        self.keepassxc_process.stdin.flush()

    def __send_command(self, command):
        with self.output_queue.mutex:
            self.output_queue.queue.clear()
            self.output_queue.all_tasks_done.notify_all()
            self.output_queue.unfinished_tasks = 0

        self.__write_command(command)

        output = []
        while True:
            line = self.get_output()
            if line is None:
                break
            output.append(line)

        return output

    def interact(self, command: str) -> [str]:
        # if command.lower() == "search":
        #     command = "ls"
        #
        # output = self.__send_command(command)[1:]
        # print(output)
        #
        # self.read_thread.join()
        output = self.__send_command(command)

        if command.lower() == 'exit':
            self.read_thread.join()

        return output

# keepass = KeepassXC()
# time.sleep(3)
# keepass.interact("search stage")