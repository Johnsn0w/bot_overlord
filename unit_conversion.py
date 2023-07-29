import re

def fahrenheit_to_celsius(s):
    # Regular expression to find Fahrenheit temperatures.
    fahrenheit_pattern = r"(^|(?<=\s|[\s,.;:!?\"\[\](){}|']))([-+]?\d*\.\d+|[-+]?\d+) ?[Ff](?=[\s,.;:!?\"\[\](){}|']|$)"
    fahrenheit_temps = re.findall(fahrenheit_pattern, s)
    
    # If no Fahrenheit temperature is found, return None
    if not fahrenheit_temps:
        return None

    # Convert the first found Fahrenheit temperature to Celsius and return it.
    fahrenheit_temp = float(fahrenheit_temps[0][1])
    celsius_temp = (fahrenheit_temp - 32) * 5.0/9.0
    
    # Round to one decimal place
    celsius_temp = round(celsius_temp, 1)

    # If the result is a whole number, remove the decimal point by converting to int
    if celsius_temp.is_integer():
        celsius_temp = int(celsius_temp)
    
    return fahrenheit_temp, celsius_temp



s_result = fahrenheit_to_celsius("!346f aoiioas ioasioioafsioa sioas oasio s325f2, ai1os as231ioa2faa fasf dg ssdg")
print(s_result)