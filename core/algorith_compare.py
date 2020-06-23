# 03.10.19


class String(str):
    # Расстояние Дамерау-Левенштейна
    def cmp_damerau_levenshtein(self, string):
        d = dict()
        len1 = len(self)
        len2 = len(string)
        for i in range(-1, len1+1):
            d[(i, -1)] = i+1
        for j in range(-1, len2+1):
            d[(-1, j)] = j+1
        for i in range(len1):
            for j in range(len2):
                if self[i] == string[j]:
                    cost = 0
                else:
                    cost = 1
                d[(i, j)] = min(d[(i-1, j)] + 1,                    # deletion
                                d[(i, j-1)] + 1,                    # insertion
                                d[(i-1, j-1)] + cost)               # substitution
                if i and j and self[i] == string[j-1] and self[i-1] == string[j]:
                    d[(i, j)] = min(d[(i, j)], d[i-2, j-2]+cost)    # transposition
        return d[len1-1, len2-1]

    def normalize(self, fn, string):
        res = fn(string)
        _max = max(len(self), len(string))
        if _max == 0:
            return 1
        return (_max-res)/_max

    # Jacquard coefficient
    def cmp_jacquard(self, string):
        a, b, c = len(self), len(string), 0
        for char in self:
            if char in string:
                c += 1
        return c/(a+b-c)

    # Расстояние Хэмминга
    def cmp_hamming(self, string):
        i, c = 0, 0
        while i < len(self) and i < len(string):
            if self[i] != string[i]:
                c += 1
            i += 1
        return c

    # Сходство Джаро
    def cmp_jaro(self, string):
        len1 = len(self)
        len2 = len(string)
        dist = int(min(len1, len2)/2)   # Theoretical distance
        cmn1 = _common_character(self, string, dist)
        cmn2 = _common_character(string, self, dist)

        i, transposition = 0, 0
        upper_bound = min(len(cmn1), len(cmn2))
        while i < upper_bound:
            if cmn1[i] != cmn2[i]:
                transposition += 1
            i += 1
        transposition /= 2
        return ((len(cmn1)/len1)+(len(cmn2)/len2)+((len(cmn1)-transposition)/len(cmn1)))/3

    # Сходство Джаро-Винклера
    def cmp_jaro_winkler(self, string, prefix_scale=0.1):
        jaro_distance = self.cmp_jaro(string)
        prefix_length = _get_prefix_len(self, string)
        return jaro_distance+(prefix_length*prefix_scale*(1-jaro_distance))

    # Коэффициент Симпсона
    def cmp_simpson(self, string):
        return self.__coefficient(string, True)

    # Коэффициет Сёренсена
    def cmp_sorensen(self, string):
        return self.__coefficient(string)

    # Побуквенное сравнивание
    def cmp_simple(self, string):
        if self == string:
            print('!')

        _dist, i, length = 0, 0, min(len(self), len(string))
        while i < length:
            j = 0
            while j+i < length:
                if self[j+i] != string[j]:
                    if _dist < j:
                        _dist = j
                    break
                j += 1
            if _dist < j:
                _dist = j
            i += 1
        return _dist/max(len(self), len(string))

    def __coefficient(self, string, simpson=False):
        pairs1 = _word_letter_pairs(self)
        pairs2 = _word_letter_pairs(string)
        intersection, union = 0, len(pairs1)+len(pairs2)-(abs(len(pairs1)-len(pairs2))*simpson)
        if union == 0:
            return 1
        for p1 in pairs1:
            for p2 in pairs2:
                if p1 == p2:
                    intersection += 1
                    pairs2.remove(p2)
                    break
        return (2*intersection)/union


def _get_prefix_len(string1, string2, min_prefix_len=4):
    i, n = 0, min([min_prefix_len, len(string1), len(string2)])
    while i < n:
        if string1[i] != string2[i]:
            return i
        i += 1
    return n


def _common_character(string1, string2, allowed_distance):
    len1 = len(string1)
    len2 = len(string2)
    i, common, temp = 0, "", string2
    while i < len1:
        match, j = False, max(0, i-allowed_distance)
        while not match and j < min(i+allowed_distance+1, len2):
            if string2[j] == string1[i]:
                match = True
            j += 1
        common += string1[i]
        temp = temp[:j]+' '+temp[j+1:]
        i += 1
    return common


def _letter_pairs(string):
    i, _pairs = 0, []
    while i < len(string)-1:
        _pairs += [string[i:i+2]]
        i += 1
    return _pairs


def _word_letter_pairs(string):
    i, _pairs = 0, []
    words = string.split(' ')
    while i < len(words):
        _pairs += _letter_pairs(words[i])
        i += 1
    return _pairs


def compare(x, s2):
    if s2 == "":
        return 0, 0, 0, 0
    return x.cmp_simple(s2), x.normalize(x.cmp_damerau_levenshtein, s2), x.cmp_jacquard(s2), x.cmp_sorensen(s2)


"""
def compare(x, s2, view=False):
    a = x.cmp_simple(s2)
    b = x.normalize(x.cmp_damerau_levenshtein, s2)
    c = x.cmp_jacquard(s2)
    d = x.cmp_sorensen(s2)
    e = x.cmp_simpson(s2)
    f = x.normalize(x.cmp_hamming, s2)
    g = x.cmp_jaro(s2)
    h = x.cmp_jaro_winkler(s2)
    if view:
        print("%-40s%.2f %.2f %.2f %.2f %.2f %.2f %.2f %.2f" % (s2, a, b, c, d, e, f, g, h))
    return a, b, c, d, e, f, g, h
"""