from PyQt5.QtCore import QSettings, QRegExp, QDate
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

def get_resp_dict_new(mit_resp=None, vri_resp=None, mieta_resp=None):
    resp_dict = {}

    if not mit_resp and not vri_resp and not mieta_resp:
        return resp_dict

    mi_reestr = ""
    mi_mitypeURL = ""
    mi_title = ""
    mi_type = ""
    mi_manufacturer = ""
    mi_modification = ""
    mi_interval = ""
    mi_manufactureNum = ""
    mi_inventoryNum = ""
    mi_manufactureYear = ""
    mi_quantity = ""
    mi_mit_id = ""

    vri_organization = ""
    vri_signCipher = ""
    vri_miOwner = ""
    vri_vrfDate = ""
    vri_validDate = ""
    vri_vriType = ""
    vri_docTitle = ""
    vri_applicable = "1"
    vri_certNum = ""
    vri_stickerNum = ""
    vri_signPass = "0"
    vri_signMi = "0"
    vri_structure = ""
    vri_briefIndicator = "0"
    vri_briefCharacteristics = ""
    vri_ranges = ""
    vri_values = ""
    vri_channels = ""
    vri_blocks = ""
    vri_additional_info = ""

    mieta_regNumber = ""
    mieta_rankСоdе = ""
    mieta_rankclass = ""
    mieta_npenumber = ""
    mieta_schematype = ""
    mieta_schemaTitle = ""

    resp_dict['vris'] = []
    resp_dict['mietas'] = []

    if vri_resp:
        # tmp_dates = list()
        # for vri in vri_resp:
        #     date = QDate().fromString(vri['result']['vriInfo']['vrfDate'], "dd.MM.yyyy")
        #     tmp_dates.append(date)
        # for vri in vri_resp:
        #     if max(tmp_dates).toString("dd.MM.yyyy") in vri['result']['vriInfo']['vrfDate']:
        #         print(vri['result']['vriInfo']['vrfDate'])
        # if 'result' in vri_resp[0]:
        #     if 'miInfo' in vri_resp[0]['result']:
        #         miInfo = vri_resp[0]['result']['miInfo']
        #         if 'etaMI' in miInfo:
        #             miInfo = miInfo['etaMI']
        #         elif 'singleMI' in miInfo:
        #             miInfo = miInfo['singleMI']
        #         elif 'partyMI' in miInfo:
        #             miInfo = miInfo['partyMI']
        #
        #         mi_reestr = miInfo.get('mitypeNumber', "")
        #         mi_mitypeURL = miInfo.get('mitypeURL', "")
        #         mi_title = miInfo.get('mitypeTitle', "")
        #         mi_type = miInfo.get('mitypeType', "")
        #         if 'modification' in miInfo and miInfo['modification']:
        #             mi_modification = miInfo['modification']
        #
        #         mi_manufactureNum = miInfo.get('manufactureNum', "")
        #         mi_inventoryNum = miInfo.get('inventoryNum', "")
        #         mi_manufactureYear = str(miInfo.get('manufactureYear', ""))
        #         mi_quantity = str(miInfo.get('quantity', ""))
        #
        #         vriInfo = vri_resp[0]['result']['vriInfo']
        #         vri_vrfDate = vriInfo.get('vrfDate', "")
        #         vri_validDate = vriInfo.get('validDate', "")
        #
        #         if vri_vrfDate and vri_validDate and not mi_interval:
        #             mi_interval = str((int(vri_validDate[-4:]) - int(vri_vrfDate[-4:])) * 12)
        #             print(f"Интервал: {mi_interval}")

        for vri in vri_resp:
            vri_FIF_id = vri.get('vri_FIF_id', "")
            vri_id = vri.get('vri_id', "")

            if 'miInfo' in vri['result']:
                miInfo = vri['result']['miInfo']
                if 'etaMI' in miInfo:
                    miInfo = miInfo['etaMI']
                elif 'singleMI' in miInfo:
                    miInfo = miInfo['singleMI']
                elif 'partyMI' in miInfo:
                    miInfo = miInfo['partyMI']

                if (not mi_reestr or mi_reestr == "None" or mi_reestr == "н/д" or mi_reestr == "нет данных") \
                        and 'mitypeNumber' in miInfo:
                    mi_reestr = str(miInfo['mitypeNumber'])
                if not mi_mitypeURL and 'mitypeURL' in miInfo:
                    mi_mitypeURL = str(miInfo['mitypeURL'])
                if (not mi_title or mi_title == "None" or mi_title == "н/д" or mi_title == "нет данных") \
                        and 'mitypeTitle' in miInfo:
                    mi_title = str(miInfo['mitypeTitle'])
                if (not mi_type or mi_type == "None" or mi_type == "н/д" or mi_type == "нет данных") \
                        and 'mitypeType' in miInfo:
                    mi_type = str(miInfo['mitypeType'])
                if (not mi_modification or mi_modification == "None" or mi_modification == "н/д" or mi_modification == "нет данных") \
                        and 'modification' in miInfo:
                    mi_modification = str(miInfo['modification'])

                if (not mi_manufactureNum or mi_manufactureNum == "None" or mi_manufactureNum == "н/д" or mi_manufactureNum == "нет данных") \
                        and 'manufactureNum' in miInfo:
                    mi_manufactureNum = str(miInfo['manufactureNum'])
                if (not mi_inventoryNum or mi_inventoryNum == "None" or mi_inventoryNum == "н/д" or mi_inventoryNum == "нет данных") \
                        and 'inventoryNum' in miInfo:
                    mi_inventoryNum = str(miInfo['inventoryNum'])
                if (not mi_manufactureYear or mi_manufactureYear == "None" or mi_manufactureYear == "н/д" or mi_manufactureYear == "нет данных") \
                        and 'manufactureYear' in miInfo:
                    mi_manufactureYear = str(miInfo['manufactureYear'])
                if not mi_quantity and 'quantity' in miInfo:
                    mi_quantity = str(miInfo['quantity'])

                if not mi_interval:
                    vriInfo = vri['result']['vriInfo']
                    vri_vrfDate = vriInfo.get('vrfDate', "")
                    vri_validDate = vriInfo.get('validDate', "")

                    if vri_vrfDate and vri_validDate:
                        mi_interval = str((int(vri_validDate[-4:]) - int(vri_vrfDate[-4:])) * 12)

            if 'result' in vri:
                if 'vriInfo' in vri['result']:
                    vriInfo = vri['result']['vriInfo']

                    vri_organization = str(vriInfo.get('organization', ""))
                    if "(" in vri_organization:
                        vri_organization = vri_organization[str(vri_organization).find("(") + 1:-1]

                    vri_signCipher = str(vriInfo.get('signCipher', ""))
                    vri_miOwner = str(vriInfo.get('miOwner', ""))
                    vri_vrfDate = str(vriInfo.get('vrfDate', ""))
                    vri_validDate = str(vriInfo.get('validDate', ""))
                    vri_vriType = str(vriInfo.get('vriType', ""))
                    if vri_vriType == "1":
                        vri_vriType = "первичная"
                    elif vri_vriType == "2":
                        vri_vriType = "периодическая"
                    vri_docTitle = str(vriInfo.get('docTitle', ""))

                    if 'applicable' in vriInfo:
                        vri_applicable = "1"

                        vri_certNum = str(vriInfo['applicable'].get('certNum', ""))
                        vri_stickerNum = str(vriInfo['applicable'].get('stickerNum', ""))
                        if 'signPass' in vriInfo['applicable'] and vriInfo['applicable']['signPass']:
                            vri_signPass = "1"
                        if 'signMi' in vriInfo['applicable'] and vriInfo['applicable']['signMi']:
                            vri_signMi = "1"

                    elif 'inapplicable' in vriInfo:
                        vri_applicable = "0"

                        vri_certNum = str(vriInfo['inapplicable'].get('noticeNum', ""))

                if 'info' in vri['result']:
                    info = vri['result']['info']

                    vri_structure = str(info.get('structure', ""))
                    if 'briefIndicator' in info and info['briefIndicator']:
                        vri_briefIndicator = "1"
                    vri_briefCharacteristics = str(info.get('briefCharacteristics', ""))
                    vri_ranges = str(info.get('ranges', ""))
                    vri_values = str(info.get('values', ""))
                    vri_channels = str(info.get('channels', ""))
                    vri_blocks = str(info.get('blocks', ""))
                    vri_additional_info = str(info.get('additional_info', ""))

            resp_dict['vris'].append({
                'vri_organization': vri_organization.replace("'", "''"),
                'vri_signCipher': vri_signCipher,
                'vri_miOwner': vri_miOwner.replace("'", "''"),
                'vri_vrfDate': vri_vrfDate,
                'vri_validDate': vri_validDate,
                'vri_vriType': vri_vriType,
                'vri_docTitle': vri_docTitle.replace("'", "''"),
                'vri_applicable': vri_applicable,
                'vri_certNum': vri_certNum.replace("'", "''"),
                'vri_stickerNum': vri_stickerNum.replace("'", "''"),
                'vri_signPass': vri_signPass,
                'vri_signMi': vri_signMi,
                'vri_structure': vri_structure.replace("'", "''"),
                'vri_briefIndicator': vri_briefIndicator,
                'vri_briefCharacteristics': vri_briefCharacteristics.replace("'", "''"),
                'vri_ranges': vri_ranges.replace("'", "''"),
                'vri_values': vri_values.replace("'", "''"),
                'vri_channels': vri_channels.replace("'", "''"),
                'vri_blocks': vri_blocks.replace("'", "''"),
                'vri_additional_info': vri_additional_info.replace("'", "''"),
                'vri_FIF_id': vri_FIF_id,
                'vri_id': vri_id,
            })

    elif mieta_resp:
        # tmp_dates = list()
        # for mieta in mieta_resp:
        #     if mieta:
        #         date = QDate().fromString(str(mieta['verification_date'])[:10], "yyyy-MM-dd")
        #         tmp_dates.append(date)
        # for mieta in mieta_resp:
        #     if max(tmp_dates).toString("yyyy-MM-dd") in mieta['verification_date']:
        #         print(mieta['verification_date'])
        mi_reestr = mieta_resp[0]['mitype_num']
        mi_title = mieta_resp[0]['mitype']
        mi_type = mieta_resp[0]['minotation']
        mi_modification = mieta_resp[0]['modification']
        mi_manufactureNum = mieta_resp[0]['factory_num']
        mi_manufactureYear = str(mieta_resp[0]['year'])

    if mit_resp:
        properties = mit_resp['properties']
        mi_mit_id = str(mit_resp['id'])
        for proper in properties:
            if proper['name'] == "foei:NameSI":
                mi_title = proper['value']
            elif proper['name'] == "foei:NumberSI":
                mi_reestr = proper['value']
            elif proper['name'] == "foei:DesignationSI":
                mi_type = ", ".join(proper['value'])
            elif proper['name'] == "foei:ManufacturerTotalSI":
                mi_manufacturer = proper['value']
            elif proper['name'] == "foei:MonthsSI" and int(proper['value']) != 0:
                mi_interval = str(proper['value'])
            elif proper['name'] == "foei:YearSI" and proper['value'] != 0:
                mi_interval = str(int(proper['value']) * 12)

    if mieta_resp:

        for mieta in mieta_resp:
            if mieta:
                vri_FIF_id = mieta.get('vri_FIF_id', "")
                vri_id = mieta.get('vri_id', "")

                mieta_regNumber = mieta['number']
                mieta_rankСоdе = mieta.get('rankcode', "")
                mieta_rankclass = mieta.get('rankclass', "")
                mieta_npenumber = mieta.get('npenumber', "")
                mieta_schematype = mieta.get('schematype', "")
                mieta_schemaTitle = mieta.get('schematitle', "")

                resp_dict['mietas'].append({
                    'mieta_number': mieta_regNumber,
                    'mieta_rankcode': mieta_rankСоdе,
                    'mieta_rankclass': mieta_rankclass,
                    'mieta_npenumber': mieta_npenumber,
                    'mieta_schematype': mieta_schematype,
                    'mieta_schematitle': mieta_schemaTitle.replace("'", "''"),
                    'vri_FIF_id': vri_FIF_id,
                    'vri_id': vri_id,
                })

    resp_dict['mi_reestr'] = mi_reestr
    resp_dict['mitypeURL'] = mi_mitypeURL
    resp_dict['mi_title'] = mi_title.replace("'", "''")
    resp_dict['mi_type'] = mi_type.replace("'", "''")
    resp_dict['mi_manufacturer'] = mi_manufacturer.replace("'", "''")
    resp_dict['mi_modification'] = mi_modification.replace("'", "''")
    resp_dict['mi_MPI'] = mi_interval
    resp_dict['mi_number'] = mi_manufactureNum.replace("'", "''")
    resp_dict['mi_inv_number'] = mi_inventoryNum.replace("'", "''")
    resp_dict['mi_manuf_year'] = mi_manufactureYear
    resp_dict['quantity'] = mi_quantity
    resp_dict['mit_id'] = mi_mit_id

    print(resp_dict)

    return resp_dict


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
