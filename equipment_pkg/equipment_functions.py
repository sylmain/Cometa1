from GLOBAL_VARS import *
import functions_pkg.functions as func
from PyQt5.QtCore import Qt, QRegExp, QDate
from PyQt5.QtGui import QStandardItem

import functions_pkg.functions as func
from GLOBAL_VARS import *


def get_dict_with_scan_results_for_db(mit_resp=None, vri_resp=None, mieta_resp=None):
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

def get_next_card_number(mi_id, meas_code, sub_meas_code, mi_dict):
    """
    создает и возвращает следующий по порядку номер карточки по определенному пользователем шаблону
    :param mi_id: id оборудования
    :param meas_code: выбранный вид измерений
    :param sub_meas_code: выбранный подвид измерений
    :return: созданный номер карточки
    """
    # сохраняем текущий номер карточки
    cur_card_number = mi_dict[mi_id]['reg_card_number'] if mi_id else ""
    # сохраняем вид измерений
    new_meas_code = "" if meas_code.startswith("- ") else meas_code[:2]
    # сохраняем подвид измерений
    new_sub_meas_code = "" if sub_meas_code.startswith("- ") else sub_meas_code[2:4]

    # если нет подвида и вида, записываем сохраненный номер и выходим
    if not new_meas_code and not new_sub_meas_code:
        return cur_card_number

    format_line = str(SETTINGS.value("format/equipment_reg_card_number"))  # шаблон номера карточки из настроек
    digit_count = str(format_line).count("N")  # количество цифр в порядковом номере
    digit_start = format_line.find("N")  # индекс первого вхождения порядкового номера

    # создаем регулярное выражение для поиска уже созданных карточек и определения последнего номера
    rx_string = format_line.replace("MM", new_meas_code)
    rx_string = rx_string.replace("SS", new_sub_meas_code)
    rx_string = rx_string.replace("N" * digit_count, "\d{" + str(digit_count) + "}")
    rx = QRegExp(f"^{rx_string}$")

    last_number = 0
    for mi_id in mi_dict:
        reg_card_number = mi_dict[mi_id]['reg_card_number']
        if rx.indexIn(reg_card_number) == 0:
            if int(str(reg_card_number)[digit_start:(digit_start + digit_count)]) > last_number:
                last_number = int(str(reg_card_number)[digit_start:(digit_start + digit_count)])

    # записываем новый номер в шаблон
    new_card_number = format_line.replace("MM", new_meas_code)
    new_card_number = new_card_number.replace("SS", new_sub_meas_code)
    prev_card_number = new_card_number.replace("N" * digit_count, str(last_number).rjust(digit_count, '0'))
    new_card_number = new_card_number.replace("N" * digit_count, str(last_number + 1).rjust(digit_count, '0'))

    # если выбран первоначальный (сохраненный) вид измерений, то записываем значение из словаря
    if prev_card_number == cur_card_number:
        return cur_card_number

    # если поле номера карточки пустое или сохраненный вид измерений отличается от текущего - меняем номер карточки
    if not cur_card_number or cur_card_number != prev_card_number:
        return new_card_number
