function print_message(message, color)
{
    message = "<p style='color: " + color +  ";' >" + message + "</p>"
    return message
}

function print_error(message)
{
    return print_message(message, "red")
}

function print_test(message)
{
    return print_message(message, "green")
}
