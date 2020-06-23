# Константы для формирования запроса
VG_RANK = 0                             # nick > 1, то self._last[][1] иначе self._last[][4]
VG_STATS = 1                            # self._last[][1]
VG_WIN_RATE = 2                         # self._last[][4] (Если nick > 1, то self._last[][-1])
VG_PICK = 3                             # self._last[][4] - всегда для 1 игрока
VG_50GAMES_DATA = 4                     # self._last[][4] (Если nick > 1, то self._last[][-1])
VG_TALENTS = 5                          # self._last[][5] - всегда для 1 игрока

# Таким образом, -1 при nick > 1 (исключения только для VG_RANK и VG_STATS)
