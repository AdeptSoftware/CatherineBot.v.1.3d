import re


# функция для расчета
def calc(a, action, b):
    if action == '^':
        return to_string(float(a) ** float(b))
    elif action == '*':
        return to_string(float(a) * float(b))
    elif action == '/':
        return to_string(float(a) / float(b))
    elif action == '%':
        return to_string(float(a) % float(b))
    elif action == '+':
        return to_string(float(a) + float(b))
    elif action == '-':
        return to_string(float(a) - float(b))
    return ""


# функция для отображения значений
def to_string(f):
    if int(f) == f:
        return str(int(f))
    return str(f)


# проверить кол-во скобок
def check_brackets(_formula):
    _count = 0
    for _sym in _formula:
        if _sym == '(':
            _count += 1
        if _sym == ')':
            _count -= 1
    if _count != 0:
        return False
    return True


# передается возможная формула, которую надо проверить и оптимизировать
# не могут быть здесь посторонние символы. Возможны: [\d+\-*/^\(\).,]
def prepare_math(_possible_formula):
    if not check_brackets(_possible_formula):
        return "!В формуле есть лишние скобки!"
    _flag = bool(False)         # ставить * до ( если не было
    _res = ""
    # предварительно оптимизируем
    _last = ""
    _c_m = 0                    # кол-во минусов подряд
    _c_p = 0                    # кол-во точек в цифре
    _num_l = bool(True)         # математический ли символ?
    for _sym in _possible_formula:
        if _sym != '(' and _sym != ' ':
            _flag = True
        if _sym == ',':
            _sym = '.'
        _num_s = bool(True)   # математический ли символ?
        if _sym in ['+', '-', '*', '/', '%', '^']:
            _num_s = False

        if _num_s or (not _num_s and (_num_l or
                                      (not _num_l and _sym == '-' and _c_m < 2))):
            if _num_s:
                if _sym == '.':
                    if _c_p < 1:
                        if not _num_l:
                            _res += '0'
                        _c_p += 1
                    else:
                        return "!В числе не может содержать больше 1 точки!"
            else:
                if _last == '.':
                    _res += '0'
                _c_p = 0

            if _sym != ' ':
                if _sym == '(' and _num_l and _flag and _last not in ['+', '-', '*', '(',
                                                                      '/', '%', '^', ')']:
                    if _last == '.':
                        _res += '0'
                        _c_p = 0
                    if _last != '':
                        _res += '*('
                        _last = '*'
                    else:
                        _res += '('
                elif _last == ')' and _num_s:
                    if _sym == '.':
                        _res += '*0.'
                        _c_p = 1
                    elif _sym == ')':
                        _res += _sym
                    else:
                        _res += '*'+_sym
                    _last = _sym
#                elif _last in ['+', '-', '*', '/', '%', '^'] and _sym == ')':
#                    return "!После: '" + _last + "' должно идти число, а не '" + _sym + "'!"
                else:
                    if _sym == '.' and _last == "":
                        __flag = False
                        for __sym in _possible_formula:
                            if (__sym not in ['.', ' ']) and __sym == '(':
                                __flag = True
                                break
                        if __flag:
                            continue
                    _res += _sym
                    _last = _sym

            if _sym == '-':
                _c_m += 1
            else:
                _c_m = 0
        else:
            return "!Недопустимая комбинация операций: '"+_last+_sym+"'!"
        _num_l = _num_s

    if _last in ['+', '-', '*', '/', '%', '^', '.']:
        if _last == '.':
            _res += '0'
        else:
            return "!Ожидалось число в конце формулы!"

    if "()" in _res:
        _res = _res.replace('()', '')

    if _res == "":
        return "!Это не формула!"
    else:
        _resA = _res
        if _res[0] in ['+', '-', '*', '/', '%', '^', '.']:
            _resA = _res[1:]
        _flag = False
        for c in _resA:
            if not ('0' <= c <= '9' or c == '.'):
                _flag = True
                break
        if not _flag:
            return "!Это просто число или некорректная формула!"     # или одинокий математический символ
    return _res


# получить строку элементов формулы
def get_element_formula(_formula):
    _res = re.findall(r'(?:\d+(?:[.,]\d+|\b)|[+\-*/^%])', _formula)
    flag = bool(False)
    for i in range(0, len(_res)):
        if flag:
            _res[i-1] = '-'+_res[i-1]
            flag = False
        if i == len(_res):
            break
        if _res[i] == '-' and (i == 0 or (i > 0 and _res[i-1] in ['+', '-', '*',
                                                                  '/', '%', '^'])):
            _res.remove(_res[i])
            flag = True
    return _res


# склеить формулу обратно
def glue_back(part, brackets):
    _s = ""
    if brackets:
        _s += "("
    for p in part:
        _s += p
    if brackets:
        _s += ")"
    return _s


def execute(_possible_formulas):
    _rc = []            # здесь будет результат вычислений
    formula = []
    for _r in _possible_formulas:
        string = prepare_math(_r)
        if not (len(string) != 0 and string[0] != '!'):
            _rc.append({"formula": _r, "result": string})
        else:
            formula.append(string)

    # производим расчет:
    for x in range(0, len(formula)):
        _rc.append({"formula": formula[x], "result": "?"})
        _exit = bool(False)
        while not _exit:
            result = re.findall(r'\([0-9+\-*/^%.]*\)', formula[x])
            if len(result) == 0:
                result = [formula[x]]
                _exit = True
            for _res in result:
                if not _exit:
                    _res = _res[1:len(_res)-1]
                part = get_element_formula(_res)
                if len(part) == 0:
                    _rc[len(_rc)-1]["result"] = '!Ошибка! Неизвестная математическая ' \
                                                'операция или число задано неверно!'
                    _exit = True
                    break
                elif len(part) == 1:
                    if part[0] == _rc[len(_rc)-1]["formula"]:
                        _rc[len(_rc) - 1]["result"] = '!Ошибка! Это не математическая операция!'
                        _exit = True
                        break
                    formula[x] = formula[x].replace('('+part[0]+')', part[0])
                    continue
                _break = bool(False)
                for group in [['^'], ['*', '/', '%'], ['+', '-']]:
                    for a in group:
                        _c = 0
                        for i in range(1, len(part), 2):
                            if part[i-_c] == a:
                                _s = glue_back(part, not _exit)
                                try:
                                    part[i+1-_c] = calc(part[i-_c-1], a, part[i-_c+1])
                                except ZeroDivisionError:
                                    formula[x] = 'Деление на ноль!'
                                    _break = True
                                    break
                                except IndexError:
                                    formula[x] = 'Формула не корректна!'
                                    _break = True
                                    break
                                part.pop(i-_c)
                                part.pop(i-_c-1)
                                _c += 2

                                flag = bool(False)
                                if not _exit:
                                    for action in ['^', '*', '/', '%', '+', '-']:
                                        if action in part:
                                            flag = True
                                            break
                                _z = glue_back(part, flag)
                                # заменяем все что в скобках на полученное число
                                formula[x] = formula[x].replace(_s, _z)
                        if _break:
                            break
                    # убрать 216^(-3)
                    if _break:
                        break
                if _break:
                    _exit = True
                    break
        if formula[x] == "":
            formula[x] = "!Результат не найден! :("
        if _rc[len(_rc)-1]["result"] == '?':
            _rc[len(_rc)-1]["result"] = formula[x]
    return _rc


# ======== ========= ========= ========= ========= ========= ========= =========
# главная функция, которую необходимо вызывать:
def main(_text):
    _text = _text.replace('÷', '/')
    _text = _text.replace(':', '/')
    _text = _text.replace('x', '*')
    _text = _text.replace('х', '*')
    _text = _text.replace('×', '*')
    result = re.findall(r'[\d(][\d+\-*/^()., ]+', _text)
    if len(result) == 0:
        return None
    try:
        return execute(result)
    except:
        return {'formula': _text, 'result': '!Невозможно корректно обработать!'}
