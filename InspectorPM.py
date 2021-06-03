import sys
import bluetooth
import matplotlib.pyplot as plt
import re
import time

def main():
    log_file = "InspectorPM.log"
    stderr_fd = sys.stderr
    sys.stderr = open(log_file, 'w')  # log the errors
    module_addr = "98:D3:51:FE:11:A8"
    
    try:
        print("Connecting target module addr " + module_addr + "...", end='')
        try:
            module_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            port = 1
            module_socket.connect((module_addr, port))
        except:
            print("Couldn't establish connection. Ended.")
            sys.stderr = stderr_fd
            sys.exit(1)
        print("\t[Done]")

        print("Gathering data...")
        data = ""
        h_time_axis = []
        d_time_axis = []
        hourly_avg_axis = []
        daily_avg_axis = []
        h_data_offset = len("Hourly average: ")
        d_data_offset = len("Daily average: ")
        msr_unit = "ug/m3"

        try:
            while True:
                partial_data = module_socket.recv(1024)
                
                if not partial_data:
                    break
                
                data += partial_data.decode("utf-8")
                
                if data[-2:] == "\r\n":
                    print(data[:-2])
                    data_copy = data

                    while "Daily" in data:
                        data = data[data.find("Daily"):]
                        data = data[d_data_offset : data.find(msr_unit)]
                        daily_avg_axis.append(data)
                        # d_time_axis.append(time.localtime(time.time()).tm_mday)
                        # d_time_axis.append(i)

                    data = data_copy

                    while "Hourly" in data:
                        data = data[data.find("Hourly"):]
                        data = data[h_data_offset : data.find(msr_unit)]
                        hourly_avg_axis.append(data)
                        # h_time_axis.append(time.localtime(time.time()).tm_hour)
                        # h_time_axis.append(i)

                    data = ""
        except OSError:
            print("Error! Closing connection...", end='')
            module_socket.close()
            sys.stderr = stderr_fd
            print("\t[Done]")
            sys.exit(2)

        print("Gathering data...\t[Done]")

        print("Closing the connection...", end='')
        module_socket.close()
        print("\t[Done]")

    except KeyboardInterrupt:
        print("Interrupted. Gathering data...\t[Done]")
        print("Closing connection...", end='')
        module_socket.close()
        print("\t[Done]")

        print("Processing graphs...")
        # parse the first "bulk" messages (if not already)
        hourly_avg_axis = list(filter(lambda x: True if "Daily" not in x
                                    else False, hourly_avg_axis))
        hourly_avg_axis = re.findall(r"[-+]?\d*\.\d+", ' '.join(hourly_avg_axis))
        hourly_avg_axis = list(map(float, hourly_avg_axis))
        daily_avg_axis = re.findall(r"[-+]?\d*\.\d+", ' '.join(daily_avg_axis))
        daily_avg_axis = list(map(float, daily_avg_axis))

        # set the time axis
        h_time_axis = range(1, len(hourly_avg_axis) + 1)
        d_time_axis = range(1, len(daily_avg_axis) + 1)
        # y-axis bounds
        try:
            min_daily = min(daily_avg_axis)
            max_daily = max(daily_avg_axis)
        except ValueError:
            print("No average per day recorded")
        try:
            min_hourly = min(hourly_avg_axis)
            max_hourly = max(hourly_avg_axis)
        except ValueError:
            print("No average per hour recorded. Exiting...", end='')
            sys.stderr = stderr_fd
            print("\t[Done]")
            exit(1)


        # plot the average density per hour
        plt.plot(h_time_axis, hourly_avg_axis)
        plt.ylim(ymin=min_hourly - 5 if min_hourly >= 5 else 0, ymax=max_hourly + 5)
        plt.xlabel("Time(h)")
        plt.ylabel("Dust density(ug/m3)")
        plt.title("Average density per hour")
        plt.show()

        # plot the average density per day
        plt.scatter(d_time_axis, daily_avg_axis)
        plt.ylim(ymin=min_daily - 5 if min_daily >= 5 else 0, ymax=max_daily + 5)
        plt.xlabel("Time(h)")
        plt.ylabel("Dust density(ug/m3)")
        plt.title("Average density per day")
        plt.show()

        # TO DO: plot the quality level

        print("\t[Done]")

    

if __name__ == '__main__':
    print("--Started execution--")
    main()
    print("--Finished execution--")
