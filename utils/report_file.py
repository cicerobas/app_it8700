from datetime import datetime


def generate_report_file(file_path, data):
    divider = "|" + "=" * 67 + "|\n"
    group = data.get("group")
    model = data.get("model")
    customer = data.get("customer")
    sn = data.get("serial_number")
    test_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    operator = data.get("operator")
    steps = data.get("steps")
    lines = []
    with open(file_path, "w") as file:
        file.write(divider)
        file.write("| CEBRA - Power Supply Test Report" + " " * 34 + "|\n")
        file.write(f"| Group: {group + ' ' * (59-len(group))}|\n")
        file.write(f"| Model: {model + ' ' * (59-len(model))}|\n")
        file.write(f"| Customer: {customer + ' ' * (56-len(customer))}|\n")
        file.write(f"| Series Nº: {sn + ' ' * (55-len(sn))}|\n")
        file.write(f"| Test Date: {test_date + ' ' * (68-13-len(test_date))}|\n")
        file.write(f"| Tested By: {operator + ' ' * (68-13-len(operator))}|\n")
        for step in steps:
            file.write(divider)
            description = step["description"]
            status = step["status"]
            lines.append(
                f"|-> {description + ' ' * (55-len(description))}{'[ PASS ]' if status else '[ FAIL ]'} |\n"
            )
            chs_line = "|" + "=" * 14
            loadcurr_line = "|Load Current: "
            upper_line = "|Upper: " + " " * 7
            lower_line = "|Lower: " + " " * 7
            outcome_line = "|Outcome: " + " " * 5
            power_line = "|Power: " + " " * 7
            for channel in step["channels"]:
                load = str(channel["load"])
                vmax = str(channel["vmax"])
                vmin = str(channel["vmin"])
                output = str("%.2f" % channel["output"])
                power = str("%.2f" % channel["power"])

                chs_line += f"[Channel {channel['channel_id']}]=="
                loadcurr_line += f"[ {load+' '*(8-len(load))}]A "
                upper_line += f"[ {vmax+' '*(8-len(vmax))}]V "
                lower_line += f"[ {vmin+' '*(8-len(vmin))}]V "
                outcome_line += f"[ {output+' '*(8-len(output))}]V "
                power_line += f"[ {power+' '*(8-len(power))}]W "

            chs_line += f"{'=' * (68 - len(chs_line))}|\n"
            loadcurr_line += f"{' ' * (68 - len(loadcurr_line))}|\n"
            upper_line += f"{' ' * (68 - len(upper_line))}|\n"
            lower_line += f"{' ' * (68 - len(lower_line))}|\n"
            outcome_line += f"{' ' * (68 - len(outcome_line))}|\n"
            power_line += f"{' ' * (68 - len(power_line))}|\n"

            lines.append(chs_line)
            lines.append(loadcurr_line)
            lines.append(upper_line)
            lines.append(lower_line)
            lines.append(outcome_line)
            lines.append(power_line)

            file.writelines(lines)
            lines.clear()

        file.write(divider)
