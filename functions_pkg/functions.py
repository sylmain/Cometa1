from PyQt5.QtCore import QDate

from functions_pkg.db_functions import MySQLConnection
from collections import defaultdict


def get_departments():
    sql_select = "SELECT * from departments ORDER BY dep_id"
    result = MySQLConnection.execute_read_query(sql_select)

    dep_dict = dict()
    dep_name_list = list()

    for dep in result:
        dep_dict[dep[0]] = {'name': dep[1],
                            'abbr': dep[2],
                            'number': dep[3],
                            'boss': dep[4],
                            'boss_assistant': dep[5],
                            'parent': dep[6],
                            'info': dep[7],
                            'boss_post': dep[8],
                            'boss_assistant_post': dep[9]}
        dep_name_list.append(dep[1])
    print("get_departments")
    return {'dep_dict': dep_dict, 'dep_name_list': dep_name_list}


def get_dep_id_from_name(dep_name, dep_dict):
    for dep_id in dep_dict:
        if dep_dict[dep_id]['name'] == dep_name:
            return dep_id
    return "0"


def get_dep_name_from_id(dep_id, dep_dict):
    if dep_id in dep_dict:
        return dep_dict[dep_id]['name']
    else:
        return ""


def get_dep_id_from_number(dep_number, dep_dict):
    for dep_id in dep_dict:
        if dep_dict[dep_id]['number'] == dep_number:
            return dep_id
    return "0"


def get_workers():
    sql_select = "SELECT * FROM workers ORDER BY worker_surname"
    result = MySQLConnection.execute_read_query(sql_select)

    worker_dict = dict()

    for worker in result:
        worker_dict[worker[0]] = {'tab_number': worker[1],
                                  'surname': worker[2],
                                  'name': worker[3],
                                  'patronymic': worker[4],
                                  'post': worker[5],
                                  'snils': worker[6],
                                  'birthday': worker[7],
                                  'birthplace': worker[8],
                                  'contract_info': worker[9],
                                  'startjob_date': worker[10],
                                  'attestations': worker[11],
                                  'education': worker[12],
                                  'email': worker[13],
                                  'info': worker[14],
                                  'phone': worker[15]}
    print("get_workers")

    return {'worker_dict': worker_dict}


def get_worker_deps():
    dep_workers_dict = defaultdict(list)
    worker_deps_dict = defaultdict(list)

    sql_select = "SELECT * from workers_departments"
    result = MySQLConnection.execute_read_query(sql_select)

    for worker_id, dep_id in result:
        dep_workers_dict[dep_id].append(worker_id)
        worker_deps_dict[worker_id].append(dep_id)
    print("get_worker_deps")

    return {'dep_workers_dict': dict(dep_workers_dict), 'worker_deps_dict': dict(worker_deps_dict)}


def get_workers_list(dep_list, worker_dict, dep_workers_dict):
    workers = set()
    worker_and_numbers = set()
    for dep_id in dep_list:
        if dep_id in dep_workers_dict:
            for worker_id in dep_workers_dict[dep_id]:
                workers.add(get_worker_fio_from_id(worker_id, worker_dict))
                worker_and_numbers.add(get_worker_fio_and_number_from_id(worker_id, worker_dict))
    return {'workers': sorted(list(workers)), 'worker_and_numbers': sorted(list(worker_and_numbers))}


def get_worker_id_from_fio(fio, worker_dict):
    for worker_id in worker_dict:
        if get_worker_fio_from_id(worker_id, worker_dict) in fio:
            return int(worker_id)
    return "0"


def get_worker_fio_from_id(worker_id, worker_dict):
    if worker_id in worker_dict:
        surname = worker_dict[worker_id]['surname']
        name = worker_dict[worker_id]['name']
        patronymic = worker_dict[worker_id]['patronymic']
        fio = surname
        if name and patronymic:
            fio = f"{surname} {name[:1]}.{patronymic[:1]}."
        elif name:
            fio = f"{surname} {name[:1]}."
        return fio
    else:
        return ""


def get_worker_fio_and_number_from_id(worker_id, worker_dict):
    if worker_id in worker_dict:
        tab_number = worker_dict[worker_id]['tab_number']
        fio = get_worker_fio_from_id(worker_id, worker_dict)
        if tab_number:
            fio = f"{fio} ({tab_number})"
        return fio
    else:
        return ""


def get_rooms():
    sql_select = "SELECT * FROM rooms ORDER BY room_number"
    result = MySQLConnection.execute_read_query(sql_select)

    room_dict = dict()
    for room in result:
        room_dict[room[0]] = {'number': room[1],
                              'name': room[2],
                              'area': room[3],
                              'resp_person': room[4],
                              'purpose': room[5],
                              'requirements': room[6],
                              'conditions': room[7],
                              'equipment': room[8],
                              'owner': room[9],
                              'personal': room[10],
                              'info': room[11]}
    print("get_rooms")

    return {'room_dict': room_dict}


def get_worker_rooms_list(worker_id, room_dict):
    worker_rooms_list = list()
    for room_id in room_dict:
        if room_dict[room_id]['resp_person'] == worker_id:
            worker_rooms_list.append(room_id)
    return worker_rooms_list


def get_room_deps():
    dep_rooms_dict = defaultdict(list)
    room_deps_dict = defaultdict(list)
    sql_select = "SELECT rooms_departments.RD_dep_id, rooms_departments.RD_room_id " \
                 "FROM rooms_departments, rooms " \
                 "WHERE rooms_departments.RD_room_id = rooms.room_id " \
                 "ORDER BY rooms.room_number"
    result = MySQLConnection.execute_read_query(sql_select)

    for dep_id, room_id in result:
        dep_rooms_dict[dep_id].append(room_id)
        room_deps_dict[room_id].append(dep_id)
    print("get_room_deps")

    return {'dep_rooms_dict': dict(dep_rooms_dict), 'room_deps_dict': dict(room_deps_dict)}


def get_rooms_list(dep_list, room_dict, dep_rooms_dict):
    rooms = set()
    for dep_id in dep_list:
        if dep_id in dep_rooms_dict:
            for room_id in dep_rooms_dict[dep_id]:
                rooms.add(get_room_number_from_id(room_id, room_dict))
    return {'rooms': sorted(list(rooms)), 'reserve': 'reserve'}


def get_room_id_from_number(room, room_dict):
    for room_id in room_dict:
        if room_dict[room_id]['number'] == room:
            return room_id
    return "0"


def get_room_number_from_id(room_id, room_dict):
    if room_id in room_dict:
        return room_dict[room_id]['number']
    else:
        return ""


def get_measure_codes():
    measure_codes_dict = dict()
    measure_codes_list = list()
    measure_sub_codes_dict = dict()
    sql_select = "SELECT * FROM measure_codes ORDER BY measure_code"
    result = MySQLConnection.execute_read_query(sql_select)
    for code in result:
        measure_codes_dict[code[0]] = code[1]
        if len(code[0]) < 4:
            measure_codes_list.append(f"{code[0]} {code[1]}")
        else:
            measure_code = code[0][:2]
            if measure_code not in measure_sub_codes_dict:
                measure_sub_codes_dict[measure_code] = list()
                measure_sub_codes_dict[measure_code].append(f"{code[0]} {code[1]}")
            else:
                measure_sub_codes_dict[measure_code].append(f"{code[0]} {code[1]}")
    print("get_measure_codes")

    return {'measure_codes_dict': measure_codes_dict, 'measure_codes_list': measure_codes_list,
            'measure_sub_codes_dict': measure_sub_codes_dict}


def get_measure_code_id_from_name(name, measure_codes):
    for code in measure_codes['measure_codes_dict']:
        if name == measure_codes['measure_codes_dict'][code]:
            return code
    return "0"


def get_measure_code_name_from_id(code_id, measure_codes):
    if code_id in measure_codes['measure_codes_dict']:
        return measure_codes['measure_codes_dict'][code_id]
    return ""


def get_mis():
    mi_dict = dict()
    set_of_mi = set()
    list_of_card_numbers = list()
    sql_select = "SELECT * FROM mis ORDER BY mi_id"
    result = MySQLConnection.execute_read_query(sql_select) or []
    for mi in result:
        mi_dict[mi[0]] = {
            'reg_card_number': mi[1],
            'measure_code': mi[2],
            'status': mi[3],
            'reestr': mi[4],
            'title': mi[5],
            'type': mi[6],
            'modification': mi[7],
            'number': mi[8],
            'inv_number': mi[9],
            'manufacturer': mi[10],
            'manuf_year': mi[11],
            'expl_year': mi[12],
            'diapazon': mi[13],
            'PG': mi[14],
            'KT': mi[15],
            'other_characteristics': mi[16],
            'MPI': mi[17],
            'purpose': mi[18],
            'responsible_person': mi[19],
            'personal': mi[20],
            'room': mi[21],
            'software_inner': mi[22],
            'software_outer': mi[23],
            'RE': mi[24],
            'pasport': mi[25],
            'MP': mi[26],
            'TO_period': mi[27],
            'owner': mi[28],
            'owner_contract': mi[29],
            'last_scan_date': mi[30]
        }
        set_of_mi.add((mi[5], mi[7], mi[8]))
        list_of_card_numbers.append(mi[1])
    print("get_mis")

    return {'mi_dict': mi_dict, 'set_of_mi': set_of_mi, 'list_of_card_numbers': list_of_card_numbers,
            'reserve': 'reserve'}


def get_mi_id_from_set_of_mi(cur_tuple, mi_dict):
    for mi_id in mi_dict:
        if mi_dict[mi_id]['title'] == cur_tuple[0] and mi_dict[mi_id]['modification'] == cur_tuple[1] and \
                mi_dict[mi_id]['number'] == cur_tuple[2]:
            return mi_id
    return ""


def get_mi_id_from_card_number(card_number, mis_dict):
    for mis_id in mis_dict:
        if mis_dict[mis_id]['reg_card_number'] == card_number:
            return mis_id
    return "0"


def get_mi_deps():
    dep_mis_dict = defaultdict(list)
    mi_deps_dict = defaultdict(list)

    sql_select = "SELECT * from mis_departments"
    result = MySQLConnection.execute_read_query(sql_select)

    for mi_id, dep_id in result:
        mi_deps_dict[mi_id].append(dep_id)
        dep_mis_dict[dep_id].append(mi_id)
    print("get_mi_deps")

    return {'mi_deps_dict': dict(mi_deps_dict), 'dep_mis_dict': dict(dep_mis_dict), 'reserve': 'reserve'}


def get_mis_vri_info():
    mis_vri_dict = dict()
    sql_select = "SELECT * FROM mis_vri_info ORDER BY vri_mi_id, vri_id"
    result = MySQLConnection.execute_read_query(sql_select) or []
    for vri_info in result:
        temp_dict = {'vri_organization': vri_info[2],
                     'vri_signCipher': vri_info[3],
                     'vri_miOwner': vri_info[4],
                     'vri_vrfDate': vri_info[5],
                     'vri_validDate': vri_info[6],
                     'vri_vriType': vri_info[7],
                     'vri_docTitle': vri_info[8],
                     'vri_applicable': vri_info[9],
                     'vri_certNum': vri_info[10],
                     'vri_stickerNum': vri_info[11],
                     'vri_signPass': vri_info[12],
                     'vri_signMi': vri_info[13],
                     'vri_inapplicable_reason': vri_info[14],
                     'vri_structure': vri_info[15],
                     'vri_briefIndicator': vri_info[16],
                     'vri_briefCharacteristics': vri_info[17],
                     'vri_ranges': vri_info[18],
                     'vri_values': vri_info[19],
                     'vri_channels': vri_info[20],
                     'vri_blocks': vri_info[21],
                     'vri_additional_info': vri_info[22],
                     'info': vri_info[23],
                     'vri_FIF_id': vri_info[24],
                     'vri_mieta_number': vri_info[25],
                     'vri_mieta_rankcode': vri_info[26],
                     'vri_mieta_rankclass': vri_info[27],
                     'vri_mieta_npenumber': vri_info[28],
                     'vri_mieta_schematype': vri_info[29],
                     'vri_mieta_schematitle': vri_info[30],
                     'vri_last_scan_date': vri_info[31],
                     'vri_last_save_date': vri_info[32]}
        if vri_info[1] not in mis_vri_dict:
            mis_vri_dict[vri_info[1]] = dict()
            mis_vri_dict[vri_info[1]][vri_info[0]] = temp_dict
        else:
            mis_vri_dict[vri_info[1]][vri_info[0]] = temp_dict
    print("get_mis_vri_info")

    return {'mis_vri_dict': mis_vri_dict, 'reserve': 'reserve'}


def get_organization_name():
    sql = f"SELECT org_short_name FROM organization_info"
    name = MySQLConnection.execute_read_query(sql)[0][0] or ""
    return name[0][0]


def get_director_name():
    sql = f"SELECT org_boss FROM organization_info"
    result = MySQLConnection.execute_read_query(sql)
    name = ""
    full_name_parts = result[0][0].split()
    if len(full_name_parts) == 1:
        name = full_name_parts[0]
    elif len(full_name_parts) == 2:
        name = f"{full_name_parts[0]} {full_name_parts[1][:1]}."
    elif len(full_name_parts) == 3:
        name = f"{full_name_parts[0]} {full_name_parts[1][:1]}.{full_name_parts[2][:1]}."
    return name


def comma_to_dot(string):
    return string.replace(",", ".")


def dot_to_comma(string):
    return string.replace(".", ",")


# ???????????????? ???????????????????? ???? ???????????????????????????????????? ?? ?????????????????????? ?????????????? ??????????????????
def dedupe(items):
    seen = set()
    for item in items:
        if item not in seen:
            yield item
            seen.add(item)


def get_formatted_date(date) -> str:
    formatted_date = QDate(date).toString("dd.MM.yyyy") if date else ""
    return formatted_date


def get_max_substring(str_1, str_2):
    SZ = int(1e5 + 4)
    hashpow = 137
    mod = int(1e9 + 7)
    p = [1]
    for i in range(SZ):
        p.append(p[-1] * hashpow % mod)

    def build_hash(s):
        h = [0]
        for c in s:
            h.append(h[-1] * hashpow + ord(c))
            h[-1] %= mod
        return h

    h1 = build_hash(str_1)
    h2 = build_hash(str_2)

    def get_hash(h, l, r):
        return (h[r] - h[l - 1] * p[r - l + 1] % mod + mod) % mod

    def get(m):
        d = {}
        for i in range(len(str_1) - m + 1):
            d[get_hash(h1, i + 1, i + m)] = i
        for i in range(len(str_2) - m + 1):
            hsh = get_hash(h2, i + 1, i + m)
            if hsh in d:
                return (d[hsh], i)
        return (-1, -1)

    lo = 0
    hi = SZ + 1
    while hi - lo > 1:
        m = lo + (hi - lo) // 2
        if get(m) != (-1, -1):
            lo = m
        else:
            hi = m
    # print(str_1[get(lo)[0]:get(lo)[0] + lo])
    # print(str_2[get(lo)[1]:get(lo)[1] + lo])
    # print(lo, get(lo))
    return lo, get(lo)[0], get(lo)[1]
