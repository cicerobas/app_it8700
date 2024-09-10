from datetime import datetime
import tempfile


def generate_report_file(data:dict):
    temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8')

    divider = "|" + "=" * 67 + "|\n"
    group = data.get("group")
    model = data.get("model")
    customer = data.get("customer")
    sn = data.get("serial_number")
    test_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    operator = data.get("operator")
    steps = data.get("steps")
    lines = []

    temp_file.write(divider)
    temp_file.write("| CEBRA - Power Supply Test Report" + " " * 34 + "|\n")
    temp_file.write(f"| Group: {group + ' ' * (59-len(group))}|\n")
    temp_file.write(f"| Model: {model + ' ' * (59-len(model))}|\n")
    temp_file.write(f"| Customer: {customer + ' ' * (56-len(customer))}|\n")
    temp_file.write(f"| Series Nº: {sn + ' ' * (55-len(sn))}|\n")
    temp_file.write(f"| Test Date: {test_date + ' ' * (68-13-len(test_date))}|\n")
    temp_file.write(f"| Tested By: {operator + ' ' * (68-13-len(operator))}|\n")
    for step in steps:
        temp_file.write(divider)
        description = step["description"]
        status = step["status"]
        type = step["type"]
        lines.append(
            f"|-> {description + ' ' * (55-len(description))}{'[ PASS ]' if status else '[ FAIL ]'} |\n"
        )
        match type:
            case 1:
                channels_line = "|" + "=" * 14
                static_load_line = "|Load Current: "
                voltage_upper_line = "|Upper: " + " " * 7
                voltage_lower_line = "|Lower: " + " " * 7
                voltage_output_line = "|Outcome: " + " " * 5
                power_line = "|Power: " + " " * 7
                for channel in step["channels"]:
                    static_load = str(channel["load"])
                    voltage_upper = str(channel["voltage_upper"])
                    voltage_lower = str(channel["voltage_lower"])
                    voltage_output = str("%.2f" % channel["voltage_output"])
                    power = str("%.2f" % channel["power"])

                    channels_line += f"[Channel {channel['channel_id']}]=="
                    static_load_line += f"[ {static_load+' '*(8-len(static_load))}]A "
                    voltage_upper_line += f"[ {voltage_upper+' '*(8-len(voltage_upper))}]V "
                    voltage_lower_line += f"[ {voltage_lower+' '*(8-len(voltage_lower))}]V "
                    voltage_output_line += f"[ {voltage_output+' '*(8-len(voltage_output))}]V "
                    power_line += f"[ {power+' '*(8-len(power))}]W "
            case 2:
                channels_line = "|" + "=" * 15
                under_voltage_line = "|Under Voltage: "
                load_upper_line = "|Upper: " + " " * 8
                load_lower_line = "|Lower: " + " " * 8
                load_limit_line = "|Outcome: " + " " * 6
                for channel in step["channels"]:
                    under_voltage = str(channel["under_voltage"])
                    load_upper = str(channel["load_upper"])
                    load_lower = str(channel["load_lower"])
                    load_limit = str(channel["load"])

                    channels_line += f"[Channel {channel['channel_id']}]=="
                    under_voltage_line += f"[ {under_voltage+' '*(8-len(under_voltage))}]V "
                    load_upper_line += f"[ {load_upper+' '*(8-len(load_upper))}]A "
                    load_lower_line += f"[ {load_lower+' '*(8-len(load_lower))}]A "
                    load_limit_line += f"[ {load_limit+' '*(8-len(load_limit))}]A "
        
        lines.append(f"{channels_line + '=' * (68 - len(channels_line))}|\n")
        match type:
            case 1:
                lines.append(f"{static_load_line + ' ' * (68 - len(static_load_line))}|\n")
                lines.append(f"{voltage_upper_line + ' ' * (68 - len(voltage_upper_line))}|\n")
                lines.append(f"{voltage_lower_line + ' ' * (68 - len(voltage_lower_line))}|\n")
                lines.append(f"{voltage_output_line + ' ' * (68 - len(voltage_output_line))}|\n")
                lines.append(f"{power_line + ' ' * (68 - len(power_line))}|\n")
            case 2:
                lines.append(f"{under_voltage_line + ' ' * (68 - len(under_voltage_line))}|\n")
                lines.append(f"{load_upper_line + ' ' * (68 - len(load_upper_line))}|\n")
                lines.append(f"{load_lower_line + ' ' * (68 - len(load_lower_line))}|\n")
                lines.append(f"{load_limit_line + ' ' * (68 - len(load_limit_line))}|\n")
                
        temp_file.writelines(lines)
        lines.clear()

    temp_file.write(divider)
    
    temp_file.seek(0)
    temp_file.flush()
    return temp_file
