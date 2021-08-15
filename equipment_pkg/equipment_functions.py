def get_temp_vri_dict(vri_resp, mieta_resp):
    cert_num = ""
    vri_dict = dict()

    if 'result' in vri_resp and 'vriInfo' in vri_resp['result']:
        vriInfo = vri_resp['result']['vriInfo']

        organization = ""
        signCipher = ""
        miOwner = ""
        vrfDate = ""
        validDate = "-"
        vri_result = "ГОДЕН"

        vriType = "периодическая"
        docTitle = ""
        applicable = "1"
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
        rankTitle = ""
        schemaTitle = ""
        npenumber = ""
        schematype = ""
        FIF_id = ""

        if 'organization' in vriInfo:
            if "(" in vriInfo['organization']:
                organization = str(vriInfo['organization'])[str(vriInfo['organization']).find("(") + 1:-1]
            else:
                organization = str(vriInfo['organization'])
        if 'signCipher' in vriInfo:
            signCipher = vriInfo['signCipher']
        if 'miOwner' in vriInfo:
            miOwner = vriInfo['miOwner']
        if 'vrfDate' in vriInfo:
            vrfDate = vriInfo['vrfDate']
        if 'applicable' in vriInfo:
            if 'certNum' in vriInfo['applicable']:
                cert_num = vriInfo['applicable']['certNum']
            if 'stickerNum' in vriInfo['applicable']:
                stickerNum = vriInfo['applicable']['stickerNum']
            if 'signPass' in vriInfo['applicable'] and vriInfo['applicable']['signPass']:
                signPass = "1"
            if 'signMi' in vriInfo['applicable'] and vriInfo['applicable']['signMi']:
                signMi = "1"
            if 'validDate' in vriInfo:
                validDate = vriInfo['validDate']
            else:
                validDate = "Бессрочно"
        elif 'inapplicable' in vriInfo:
            applicable = "0"
            if 'noticeNum' in vriInfo['inapplicable']:
                cert_num = vriInfo['inapplicable']['noticeNum']
            vri_result = "БРАК"
        if 'vriType' in vriInfo and str(vriInfo['vriType']) == "1":
            vriType = "первичная"
        if 'docTitle' in vriInfo:
            docTitle = vriInfo['docTitle']

        if 'info' in vri_resp['result']:
            info = vri_resp['result']['info']
            if 'structure' in info:
                structure = info['structure']
            if 'briefIndicator' in info and info['briefIndicator']:
                briefIndicator = "1"
            if 'briefCharacteristics' in info:
                briefCharacteristics = info['briefCharacteristics']
            if 'ranges' in info:
                ranges = info['ranges']
            if 'values' in info:
                values = info['values']
            if 'channels' in info:
                channels = info['channels']
            if 'blocks' in info:
                blocks = info['blocks']
            if 'additional_info' in info:
                additional_info = info['additional_info']

        if mieta_resp and 'result' in mieta_resp:
            result = mieta_resp['result']
            if 'number' in result:
                regNumber = result['number']
            if 'rankcode' in result:
                rankСоdе = result['rankcode']
            if 'rankclass' in result:
                rankTitle = result['rankclass']
            if 'npenumber' in result:
                npenumber = result['npenumber']
            if 'schematype' in result:
                schematype = result['schematype']
            if 'schematitle' in result:
                schemaTitle = result['schematitle']
        elif 'miInfo' in vri_resp['result'] and 'etaMI' in vri_resp['result']['miInfo']:
            etaMI = vri_resp['result']['miInfo']['etaMI']
            if 'regNumber' in etaMI:
                regNumber = etaMI['regNumber']
            if 'rankСоdе' in etaMI:
                rankСоdе = etaMI['rankСоdе']
            if 'rankTitle' in etaMI:
                rankTitle = etaMI['rankTitle']
            if 'schemaTitle' in etaMI:
                schemaTitle = etaMI['schemaTitle']

        if cert_num:
            vri_dict = {'organization': organization,
                        'signCipher': signCipher,
                        'miOwner': miOwner,
                        'vrfDate': vrfDate,
                        'validDate': validDate,
                        'vriType': vriType,
                        'docTitle': docTitle,
                        'applicable': applicable,
                        'certNum': cert_num,
                        'stickerNum': stickerNum,
                        'signPass': signPass,
                        'signMi': signMi,
                        'inapplicable_reason': "",
                        'structure': structure,
                        'briefIndicator': briefIndicator,
                        'briefCharacteristics': briefCharacteristics,
                        'ranges': ranges,
                        'values': values,
                        'channels': channels,
                        'blocks': blocks,
                        'additional_info': additional_info,
                        'info': "",
                        'regNumber': regNumber,
                        'rankСоdе': rankСоdе,
                        'rankTitle': rankTitle,
                        'npenumber': npenumber,
                        'schematype': schematype,
                        'schemaTitle': schemaTitle}
    return vri_result, cert_num, vri_dict


# СЛОВАРЬ ДЛЯ ЗАПОЛНЕНИЯ ОБЩИХ ДАННЫХ О СИ
def get_mi_dict(mit_resp=None, vri_resp=None):
    number = notation = manufacturer = MPI = ""
    hasMPI = True
    title = manufactureNum = inventoryNum = manufactureYear = modification = ""
    if vri_resp:
        if 'result' in vri_resp and 'miInfo' in vri_resp['result']:
            miInfo = vri_resp['result']['miInfo']
            if 'etaMI' in miInfo:
                miInfo = miInfo['etaMI']
            elif 'singleMI' in miInfo:
                miInfo = miInfo['singleMI']
            elif 'partyMI' in miInfo:
                miInfo = miInfo['partyMI']

            if 'mitypeTitle' in miInfo:
                title = miInfo['mitypeTitle']
            if 'manufactureNum' in miInfo:
                manufactureNum = miInfo['manufactureNum']
            if 'inventoryNum' in miInfo:
                inventoryNum = miInfo['inventoryNum']
            if 'manufactureYear' in miInfo:
                manufactureYear = str(miInfo['manufactureYear'])
            if 'modification' in miInfo:
                modification = miInfo['modification']
                notation = modification
            # вычисляем межповерочный интервал по датам поверки
            if 'vriInfo' in vri_resp['result']:
                vriInfo = vri_resp['result']['vriInfo']
                if 'vrfDate' in vriInfo and 'validDate' in vriInfo:
                    start_date = vriInfo['vrfDate']
                    end_date = vriInfo['validDate']
                    MPI = str((int(end_date[-4:]) - int(start_date[-4:])) * 12)

    # ЕСЛИ СИ В РЕЕСТРЕ
    if mit_resp:
        if 'general' in mit_resp:
            general = mit_resp['general']
            if 'number' in general:
                number = general['number']
            if 'title' in general:
                title = general['title']
            if 'notation' in general:
                notation = " ,".join(general['notation'])
        if 'manufacturer' in mit_resp:
            manufacturer_list = list()
            if 'title' in mit_resp['manufacturer'][0]:
                manufacturer_list.append(mit_resp['manufacturer'][0]['title'])
            if 'country' in mit_resp['manufacturer'][0]:
                manufacturer_list.append(mit_resp['manufacturer'][0]['country'])
            if 'locality' in mit_resp['manufacturer'][0]:
                manufacturer_list.append(mit_resp['manufacturer'][0]['locality'])
            manufacturer = ", ".join(manufacturer_list)
        if 'mit' in mit_resp:
            mit = mit_resp['mit']
            if 'interval' in mit:
                for word in mit['interval'].split(" "):
                    if word.isdigit():
                        if "мес" in mit['interval']:
                            MPI = str(int(word))
                        else:
                            MPI = str(int(word) * 12)

            if 'period' in mit and (mit['period'] != "Да" and mit['period'] != "да"):
                hasMPI = False
                MPI = ""

    mit_dict = {'number': number,
                'title': title,
                'manufactureNum': manufactureNum,
                'notation': notation,
                'modification': modification,
                'inventoryNum': inventoryNum,
                'manufacturer': manufacturer,
                'manufactureYear': manufactureYear,
                'MPI': MPI,
                'hasMPI': hasMPI}
    return mit_dict


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
    print(set_of_vri)
    return set_of_vri
