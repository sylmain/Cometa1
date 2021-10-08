from PyQt5.QtCore import QSettings, QRegExp
from GLOBAL_VARS import *


# СЛОВАРЬ РЕЗУЛЬТАТОВ ПОИСКА В АРШИН
def get_resp_dict(mit_resp=None, vri_resp=None, mieta_resp=None):
    resp_dict = {}

    if not mit_resp and not vri_resp and not mieta_resp:
        return resp_dict

    number = ""
    mitypeURL = ""
    title = ""
    notation = ""
    manufacturer = ""
    modification = ""
    interval = ""
    manufactureNum = ""
    inventoryNum = ""
    manufactureYear = ""
    quantity = ""

    organization = ""
    signCipher = ""
    miOwner = ""
    vrfDate = ""
    validDate = ""
    vriType = ""
    docTitle = ""
    applicable = "1"
    certNum = ""
    stickerNum = ""
    signPass = "0"
    signMi = "0"
    structure = ""
    briefIndicator = "0"
    briefCharacteristics = ""
    ranges = ""
    values = ""
    channels = ""
    blocks = ""
    additional_info = ""

    regNumber = ""
    rankСоdе = ""
    rankclass = ""
    npenumber = ""
    schematype = ""
    schemaTitle = ""

    vri_id_list = []

    if vri_resp:
        if 'result' in vri_resp[0]:
            if 'miInfo' in vri_resp[0]['result']:
                miInfo = vri_resp[0]['result']['miInfo']
                if 'etaMI' in miInfo:
                    miInfo = miInfo['etaMI']
                elif 'singleMI' in miInfo:
                    miInfo = miInfo['singleMI']
                elif 'partyMI' in miInfo:
                    miInfo = miInfo['partyMI']

                number = miInfo.get('mitypeNumber', "")
                mitypeURL = miInfo.get('mitypeURL', "")
                title = miInfo.get('mitypeTitle', "")
                notation = miInfo.get('mitypeType', "")
                modification = miInfo.get('modification', "")

                manufactureNum = miInfo.get('manufactureNum', "")
                inventoryNum = miInfo.get('inventoryNum', "")
                manufactureYear = str(miInfo.get('manufactureYear', ""))
                quantity = str(miInfo.get('quantity', ""))

        resp_dict['vris'] = []
        for vri in vri_resp:
            vri_FIF_id = vri.get('vri_FIF_id', "")
            vri_id = vri.get('vri_id', "")
            if 'result' in vri:
                if 'vriInfo' in vri['result']:
                    vriInfo = vri['result']['vriInfo']

                    organization = vriInfo.get('organization', "")
                    if "(" in organization:
                        organization = str(organization)[str(organization).find("(") + 1:-1]
                    else:
                        organization = str(organization)
                    signCipher = vriInfo.get('signCipher', "")
                    miOwner = vriInfo.get('miOwner', "")
                    vrfDate = vriInfo.get('vrfDate', "")
                    validDate = vriInfo.get('validDate', "")
                    vriType = vriInfo.get('vriType', "")
                    if vriType == "1":
                        vriType = "первичная"
                    elif vriType == "2":
                        vriType = "периодическая"
                    docTitle = vriInfo.get('docTitle', "")

                    if 'applicable' in vriInfo:
                        applicable = "1"

                        certNum = vriInfo['applicable'].get('certNum', "")
                        stickerNum = vriInfo['applicable'].get('stickerNum', "")
                        if 'signPass' in vriInfo['applicable'] and vriInfo['applicable']['signPass']:
                            signPass = "1"
                        if 'signMi' in vriInfo['applicable'] and vriInfo['applicable']['signMi']:
                            signMi = "1"

                    elif 'inapplicable' in vriInfo:
                        applicable = "0"

                        certNum = vriInfo['inapplicable'].get('noticeNum', "")

                    if vrfDate and validDate and not interval:
                        interval = str((int(validDate[-4:]) - int(vrfDate[-4:])) * 12)
                        print(f"Интервал: {interval}")

                if 'info' in vri['result']:
                    info = vri['result']['info']

                    structure = info.get('structure', "")
                    if 'briefIndicator' in info and info['briefIndicator']:
                        briefIndicator = "1"
                    briefCharacteristics = info.get('briefCharacteristics', "")
                    ranges = info.get('ranges', "")
                    values = info.get('values', "")
                    channels = info.get('channels', "")
                    blocks = info.get('blocks', "")
                    additional_info = info.get('additional_info', "")

            resp_dict['vris'].append({
                'vri_organization': organization.replace("'", "''"),
                'vri_signCipher': signCipher,
                'vri_miOwner': miOwner.replace("'", "''"),
                'vri_vrfDate': vrfDate,
                'vri_validDate': validDate,
                'vri_vriType': vriType,
                'vri_docTitle': docTitle.replace("'", "''"),
                'vri_applicable': applicable,
                'vri_certNum': certNum.replace("'", "''"),
                'vri_stickerNum': stickerNum.replace("'", "''"),
                'vri_signPass': signPass,
                'vri_signMi': signMi,
                'vri_structure': structure.replace("'", "''"),
                'vri_briefIndicator': briefIndicator,
                'vri_briefCharacteristics': briefCharacteristics.replace("'", "''"),
                'vri_ranges': ranges.replace("'", "''"),
                'vri_values': values.replace("'", "''"),
                'vri_channels': channels.replace("'", "''"),
                'vri_blocks': blocks.replace("'", "''"),
                'vri_additional_info': additional_info.replace("'", "''"),
                'vri_FIF_id': vri_FIF_id,
                'vri_id': vri_id,
            })

    elif mieta_resp:
        if 'result' in mieta_resp[0]:
            result = mieta_resp[0]['result']

            number = result.get('mitype_num', "")
            title = result.get('Mitype', "")
            notation = result.get('minotation', "")
            modification = result.get('modification', "")
            manufactureNum = result.get('factory_num', "")
            manufactureYear = str(result.get('year', ""))

    if mit_resp:
        if 'general' in mit_resp:
            general = mit_resp['general']

            number = general.get('number', "")
            title = general.get('title', "")
            notation = ", ".join(general.get('notation', []))

        if 'manufacturer' in mit_resp:
            manuf = mit_resp['manufacturer'][0]

            manufacturer_list = list()
            if 'title' in manuf:
                manufacturer_list.append(manuf['title'])
            if 'country' in manuf:
                manufacturer_list.append(manuf['country'])
            if 'locality' in manuf:
                manufacturer_list.append(manuf['locality'])
            manufacturer = ", ".join(manufacturer_list)

        if 'mit' in mit_resp:
            mit = mit_resp['mit']

            # if 'period' in mit and (mit['period'] != "Да" and mit['period'] != "да"):
            #     if not interval:
            #         interval = ""

            if 'interval' in mit:
                for word in mit['interval'].split(" "):
                    if word.isdigit():
                        if "мес" in mit['interval']:
                            interval = str(int(word))
                        elif int(word) < 20:
                            interval = str(int(word) * 12)

    if mieta_resp:
        resp_dict['mietas'] = []
        for mieta in mieta_resp:
            vri_id = mieta.get('vri_id', "")
            if 'result' in mieta:
                result = mieta['result']

                regNumber = result.get('number', "")
                rankСоdе = result.get('rankcode', "")
                rankclass = result.get('rankclass', "")
                npenumber = result.get('npenumber', "")
                schematype = result.get('schematype', "")
                schemaTitle = result.get('schematitle', "")

                if 'cresults' in result:
                    for cresult in result['cresults']:
                        vri_id_list.append(cresult['vri_id'])
            resp_dict['mietas'].append({
                'mieta_number': regNumber,
                'mieta_rankcode': rankСоdе,
                'mieta_rankclass': rankclass,
                'mieta_npenumber': npenumber,
                'mieta_schematype': schematype,
                'mieta_schematitle': schemaTitle.replace("'", "''"),
                'vri_id': vri_id,
                'vri_id_list': vri_id_list
            })

    resp_dict['mi_reestr'] = number
    resp_dict['mitypeURL'] = mitypeURL
    resp_dict['mi_title'] = title.replace("'", "''")
    resp_dict['mi_type'] = notation.replace("'", "''")
    resp_dict['mi_manufacturer'] = manufacturer.replace("'", "''")
    resp_dict['mi_modification'] = modification.replace("'", "''")
    resp_dict['mi_MPI'] = interval
    resp_dict['mi_number'] = manufactureNum.replace("'", "''")
    resp_dict['mi_inv_number'] = inventoryNum.replace("'", "''")
    resp_dict['mi_manuf_year'] = manufactureYear
    resp_dict['quantity'] = quantity

    print(resp_dict)

    return resp_dict


def get_temp_set_of_vri_from_mieta(mieta_resp):
    set_of_vri = set()
    if 'result' in mieta_resp:
        result = mieta_resp['result']
        mieta_number = mieta_vrf_date = mieta_cert_number = vri_id = ""
        if 'number' in result:
            mieta_number = result['number']
        if 'cresults' in result:
            for cresult in result['cresults']:
                if 'verification_date' in cresult:
                    mieta_vrf_date = cresult['verification_date']
                if 'result_docnum' in cresult:
                    mieta_cert_number = cresult['result_docnum']
                if 'vri_id' in cresult:
                    vri_id = cresult['vri_id']
                set_of_vri.add((mieta_vrf_date, mieta_cert_number, mieta_number))
    # print(set_of_vri)
    return set_of_vri


def get_next_card_number(list_of_card_numbers, new_meas_code="", new_sub_meas_code=""):
    format_line = str(SETTINGS.value("format/equipment_reg_card_number"))

    # определяем разрядность порядкового номера и первое вхождение
    digit_count = str(format_line).count("N")
    digit_start = format_line.find("N")
    # создаем регулярное выражение
    rx_string = format_line.replace("MM", new_meas_code)
    rx_string = rx_string.replace("SS", new_sub_meas_code)
    rx_string = rx_string.replace("N" * digit_count, "\d{" + str(digit_count) + "}")
    rx = QRegExp(f"^{rx_string}$")

    new_number = 1

    # создаем текущий список сохраненных таких же видов измерений (только порядковые номера) и сортируем его
    order_numbers = list()
    for meas_code in list_of_card_numbers:
        if rx.indexIn(meas_code) == 0:
            order_numbers.append(int(str(meas_code)[digit_start:(digit_start + digit_count)]))
    order_numbers.sort()

    # если список не пустой, берем номер, следующий за последним
    if order_numbers:
        new_number = order_numbers[len(order_numbers) - 1] + 1

    # записываем новый номер в заданный пользователем формат
    new_number_string = str(format_line).replace("MM", new_meas_code)
    new_number_string = new_number_string.replace("SS", new_sub_meas_code)
    temp_str = ""
    for i in range(digit_count):
        temp_str = f"{temp_str}N"
    cur_number_string = new_number_string.replace(temp_str, str(new_number - 1).rjust(digit_count, '0'))
    new_number_string = new_number_string.replace(temp_str, str(new_number).rjust(digit_count, '0'))
    return new_number_string, cur_number_string
