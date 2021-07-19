from functions_pkg.db_functions import MySQLConnection


def get_departments():
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()

    sql_select = "SELECT * from departments ORDER BY dep_id"
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    dep_dict = dict()
    dep_name_list = list()

    for dep in result:
        dep_dict[str(dep[0])] = {'name': dep[1],
                                 'abbr': dep[2],
                                 'number': dep[3],
                                 'boss': str(dep[4]),
                                 'boss_assistant': str(dep[5]),
                                 'parent': str(dep[6]),
                                 'info': dep[7],
                                 'boss_post': dep[8],
                                 'boss_assistant_post': dep[9]}
        dep_name_list.append(dep[1])
    return {'dep_dict': dep_dict, 'dep_name_list': dep_name_list, 'reserve': 'reserve'}


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


def get_workers():
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()

    sql_select = "SELECT * FROM workers ORDER BY worker_surname"
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    worker_dict = dict()

    for worker in result:
        worker_dict[str(worker[0])] = {'tab_number': worker[1],
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

    return {'worker_dict': worker_dict, 'reserve': 'reserve'}


def get_worker_deps():
    dep_workers_dict = dict()
    worker_deps_dict = dict()
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()

    sql_select = "SELECT * from workers_departments"
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    for dep_worker in result:
        # формирование словаря отдел - много сотрудников
        if str(dep_worker[1]) not in dep_workers_dict:
            dep_workers_dict[str(dep_worker[1])] = [str(dep_worker[0])]
        else:
            dep_workers_dict[str(dep_worker[1])].append(str(dep_worker[0]))

        # формирование словаря сотрудник - много отделов
        if str(dep_worker[0]) not in worker_deps_dict:
            worker_deps_dict[str(dep_worker[0])] = [str(dep_worker[1])]
        else:
            worker_deps_dict[str(dep_worker[0])].append(str(dep_worker[1]))

    return {'dep_workers_dict': dep_workers_dict, 'worker_deps_dict': worker_deps_dict, 'reserve': 'reserve'}


def get_workers_list(dep_list, worker_dict, dep_workers_dict):
    workers = set()
    worker_and_numbers = set()
    for dep_id in dep_list:
        if dep_id in dep_workers_dict:
            for worker_id in dep_workers_dict[dep_id]:
                workers.add(get_worker_fio_from_id(worker_id, worker_dict))
                worker_and_numbers.add(get_worker_fio_and_number_from_id(worker_id, worker_dict))
    return {'workers': sorted(list(workers)), 'worker_and_numbers': sorted(list(worker_and_numbers)),
            'reserve': 'reserve'}


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
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()

    sql_select = "SELECT * FROM rooms"
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    room_dict = dict()
    for room in result:
        room_dict[str(room[0])] = {'number': room[1],
                                   'name': room[2],
                                   'area': str(room[3]),
                                   'resp_person': str(room[4]),
                                   'purpose': room[5],
                                   'requirements': room[6],
                                   'conditions': room[7],
                                   'equipment': room[8],
                                   'owner': room[9],
                                   'personal': room[10],
                                   'info': room[11]}
    return {'room_dict': room_dict, 'reserve': 'reserve'}


def get_worker_rooms_list(worker_id, room_dict):
    worker_rooms_list = list()
    for room_id in room_dict:
        if room_dict[room_id]['resp_person'] == worker_id:
            worker_rooms_list.append(room_id)
    return worker_rooms_list


def get_room_deps():
    dep_rooms_dict = dict()
    room_deps_dict = dict()
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()

    sql_select = "SELECT * from rooms_departments"
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    for dep_room in result:
        # формирование словаря отдел - много комнат
        if str(dep_room[1]) not in dep_rooms_dict:
            dep_rooms_dict[str(dep_room[1])] = [str(dep_room[0])]
        else:
            dep_rooms_dict[str(dep_room[1])].append(str(dep_room[0]))

        # формирование словаря комната - много отделов
        if str(dep_room[0]) not in room_deps_dict:
            room_deps_dict[str(dep_room[0])] = [str(dep_room[1])]
        else:
            room_deps_dict[str(dep_room[0])].append(str(dep_room[1]))

    return {'dep_rooms_dict': dep_rooms_dict, 'room_deps_dict': room_deps_dict, 'reserve': 'reserve'}


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


def get_room_number_from_id(room, room_dict):
    if room in room_dict:
        return room_dict[room]['number']
    else:
        return ""


def get_measure_codes():
    measure_codes = dict()
    sql_select = "SELECT * FROM measure_codes ORDER BY measure_code"
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()
    for code in result:
        measure_codes[str(code[0])] = {'code': code[1], 'name': code[2]}
    return {'measure_codes_dict': measure_codes}


def get_measure_code_id_from_name(name, measure_codes_dict):
    for code in measure_codes_dict:
        if name == f"{measure_codes_dict[code]['code']} {measure_codes_dict[code]['name']}":
            return code
    return "0"


def get_measure_code_name_from_id(id, measure_codes_dict):
    if id in measure_codes_dict:
        return f"{measure_codes_dict[id]['code']} {measure_codes_dict[id]['name']}"
    return ""


def get_measure_code_from_id(id, measure_codes_dict):
    if id in measure_codes_dict:
        return f"{measure_codes_dict[id]['code']}"
    return ""


def get_mis():
    mis_dict = dict()
    sql_select = "SELECT * FROM mis ORDER BY mi_measure_code"
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()
    for mi in result:
        mis_dict[str(mi[0])] = {'reg_card_number': mi[1],
                                'measure_code': str(mi[2]),
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
                                'responsible_person': str(mi[19]),
                                'personal': mi[20],
                                'room': str(mi[21]),
                                'software_inner': mi[22],
                                'software_outer': mi[23],
                                'RE': str(mi[24]),
                                'pasport': str(mi[25]),
                                'MP': str(mi[26]),
                                'TO_period': mi[27],
                                'owner': mi[28],
                                'owner_contract': mi[29]}
    # `mi_id`, `mis_reg_card_number`, `mi_measure_code`, `mi_status`, `mi_reestr`, `mi_title`,
    #         `mi_modification`, `mi_number`, `mi_inv_number`, `mi_manufacturer`, `mi_manuf_year`, `mi_expl_year`,
    #         `mi_diapazon`, `mi_PG`, `mi_KT`, `mi_other_characteristics`, `mi_MPI`, `mi_purpose`,
    #         `mi_responsible_person`, `mi_personal`, `mi_room`, `mi_software_inner`, `mi_software_outer`, `mi_RE`,
    #         `mi_pasport`, `mi_MP`, `mi_TO_period`)

    return {'mis_dict': mis_dict, 'reserve': 'reserve'}


def get_mis_id_from_card_number(card_number, mis_dict):
    for mis_id in mis_dict:
        if mis_dict[mis_id]['reg_card_number'] == card_number:
            return mis_id
    return "0"


def get_mi_deps():
    dep_mis_dict = dict()
    mi_deps_dict = dict()

    sql_select = "SELECT * from mis_departments"
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()

    for mi_dep in result:

        # формирование словаря "прибор - много отделов"
        if str(mi_dep[0]) not in mi_deps_dict:
            mi_deps_dict[str(mi_dep[0])] = [str(mi_dep[1])]
        else:
            mi_deps_dict[str(mi_dep[0])].append(str(mi_dep[1]))

        # формирование словаря "отдел - много приборов"
        if str(mi_dep[1]) not in dep_mis_dict:
            dep_mis_dict[str(mi_dep[1])] = [str(mi_dep[0])]
        else:
            dep_mis_dict[str(mi_dep[1])].append(str(mi_dep[0]))

    return {'mi_deps_dict': mi_deps_dict, 'dep_mis_dict': dep_mis_dict, 'reserve': 'reserve'}


def get_mietas():
    mietas_dict = dict()
    sql_select = "SELECT * FROM mietas"
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()
    for mieta in result:
        mietas_dict[str(mieta[0])] = {'mi_id': str(mieta[1]),
                                      'number': mieta[2],
                                      'rankcode': mieta[3],
                                      'npenumber': mieta[4],
                                      'schematype': mieta[5],
                                      'schematitle': mieta[6],
                                      'rankclass': mieta[7]}

    return {'mietas_dict': mietas_dict, 'reserve': 'reserve'}


def get_mis_vri_info():
    mis_vri_dict = dict()
    sql_select = "SELECT * FROM mis_vri_info ORDER BY vri_mi_id"
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    result = MySQLConnection.execute_read_query(connection, sql_select)
    connection.close()
    for vri_info in result:
        temp_dict = {'organization': vri_info[2],
                     'signCipher': vri_info[3],
                     'miOwner': vri_info[4],
                     'vrfDate': vri_info[5],
                     'validDate': vri_info[6],
                     'vriType': vri_info[7],
                     'docTitle': vri_info[8],
                     'applicable': str(vri_info[9]),
                     'certNum': vri_info[10],
                     'stickerNum': vri_info[11],
                     'signPass': str(vri_info[12]),
                     'signMi': str(vri_info[13]),
                     'inapplicable_reason': vri_info[14],
                     'structure': vri_info[15],
                     'briefIndicator': str(vri_info[16]),
                     'briefCharacteristics': vri_info[17],
                     'ranges': vri_info[18],
                     'values': vri_info[19],
                     'channels': vri_info[20],
                     'blocks': vri_info[21],
                     'additional_info': vri_info[22],
                     'info': vri_info[23]}
        if str(vri_info[1]) not in mis_vri_dict:
            mis_vri_dict[str(vri_info[1])] = dict()
            mis_vri_dict[str(vri_info[1])][str(vri_info[0])] = temp_dict
        else:
            mis_vri_dict[str(vri_info[1])][str(vri_info[0])] = temp_dict

    return {'mis_vri_dict': mis_vri_dict, 'reserve': 'reserve'}


def get_organization_name():
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    sql_string = f"SELECT org_short_name FROM organization_info"
    name = MySQLConnection.execute_read_query(connection, sql_string)
    connection.close()
    return name[0][0]


def get_director_name():
    MySQLConnection.verify_connection()
    connection = MySQLConnection.create_connection()
    sql_string = f"SELECT org_boss FROM organization_info"
    result = MySQLConnection.execute_read_query(connection, sql_string)
    connection.close()
    name = ""
    full_name = str(result[0][0])
    full_name_parts = full_name.split()
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
