def manual_parsing(user_input):
    if 'nps' in user_input:
        for i in user_input:
            if i.isdigit():
                return ['nps',i, i+1]



