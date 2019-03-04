# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import logging
import pytesseract
from datetime import datetime
from .otsu import OtsuBinarize
_logger = logging.getLogger(__name__)


class Bitmap2Text(object):

    def _checkDigits(self, toVerify):
        m = (7, 3, 1)
        n = 0

        for i in range(len(toVerify)):
            if toVerify[i].isdigit():
                n += (toVerify[i] - '0') * m[i % 3]
            elif toVerify[i].isalpha():
                n += (toVerify[i] - 'A').upper() * m[i % 3]
            else:
                return -1
        return n % 10

    def _getNifNieLetter(self, nif):
        # Extraer letra del NIF
        letras = "TRWAGMYFPDXBNJZSQVHLCKE"
        dni = int(nif) % 23
        return letras[dni:dni + 1]

    def _isNifNie(self, nif):
        # si es NIE, eliminar la x,y,z inicial para tratarlo como nif
        if nif[0].upper() == "X" or nif[0].upper() == "Y" \
                or nif[0].upper() == "Z":
            nif = nif[1:]

        m = re.search(
            "(\\d{1,8})([TRWAGMYFPDXBNJZSQVHLCKEtrwagmyfpdxbnjzsqvhlcke])",
            nif)
        if m:
            return self._getNifNieLetter(m[1]).upper() == m.group(2).upper()
        else:
            return False

    def run(self, bitmap):
        binarizedImage = OtsuBinarize().run(bitmap)

        recognizedText = pytesseract.image_to_string(
            binarizedImage,
            lang="OCRB",
            config="-c load_system_dawg=F \
                    -c load_freq_dawg=F \
                    -c load_unambig_dawg=F \
                    -c load_number_dawg=F \
                    -c load_fixed_length_dawgs=F\
                    -c load_bigram_dawg=F \
                    -c wordrec_enable_assoc=F \
                    -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")

        _logger.info("Readed:\n" + recognizedText)

        # Possible Values
        possibleSexValues = ('F', 'M', '<')

        # PARSE OCR-B Data
        lines = recognizedText.splitlines()
        result = {}
        try:
            if '<' != lines[0][len(lines[0])] - 7:
                # DNIe
                zones = [
                    (0, 2),     # Tipo
                    (2, 5),     # Nacion
                    (5, 14),    # Numero de Serie Tarjeta
                    (14, 15),   # Digito Control: Numero de Serie Tarjeta
                    (15, 24),   # Numero DNI

                    (0, 6),     # Fecha Nacimiento
                    (6, 7),     # Digito Control: Fecha Nacimiento
                    (7, 8),     # Sexo (M/F)
                    (8, 14),    # Fecha Caducidad
                    (14, 15),   # Digito Control: Fecha Caducidad
                    (15, 18),   # Nacionalidad
                    (29, 30),   # Digito Control Maestro

                    (0, 30),    # Nombre
                ]

                zoneCardNumber = lines[0][zones[2][0]:zones[2][1]]
                zoneCardNumberVer = lines[0][zones[3][0]:zones[3][1]]
                zoneDNI = lines[0][zones[4][0]:zones[4][1]]
                zoneBirthDate = lines[1][zones[5][0]:zones[5][1]]
                zoneBirthDateVer = lines[1][zones[6][0]:zones[6][1]]
                zoneSex = lines[1][zones[7][0]:zones[7][1]]
                zoneOutDate = lines[1][zones[8][0]:zones[8][1]]
                zoneOutDateVer = lines[1][zones[9][0]:zones[9][1]]
                zoneNation = lines[1][zones[10][0]:zones[10][1]]
                zoneName = lines[2][zones[12][0]:zones[12][1]]

                # Basic Info
                DNIReaded = self._isNifNie(zoneDNI)

                # Verify Card Number
                verificationCode = self._checkDigits(zoneCardNumber)
                verCode = int(zoneCardNumberVer)
                CardNumberReaded = (verificationCode == verCode)

                # Verify BirthDate
                verificationCode = self._checkDigits(zoneBirthDate)
                verCode = int(zoneBirthDateVer)
                DateBirthReaded = (verificationCode == verCode)

                # Verify OutDate
                verificationCode = self._checkDigits(zoneOutDate)
                verCode = int(zoneOutDateVer)
                OutDateReaded = (verificationCode == verCode)

                # Verify Sex
                SexReaded = zoneSex in possibleSexValues

                # Verify Master
                toVerify = zoneCardNumber + zoneCardNumberVer + zoneDNI \
                    + zoneBirthDate + zoneBirthDateVer + zoneOutDate \
                    + zoneOutDateVer
                verificationCode = self._checkDigits(toVerify)
                verCode = int(lines[1][zones[11][0]:zones[11][1]])
                MasterVerificationReaded = (verificationCode == verCode)

                if CardNumberReaded and DateBirthReaded and OutDateReaded \
                        and MasterVerificationReaded and DNIReaded \
                        and SexReaded:
                    result.update({
                        'result': recognizedText,
                        'name': zoneName.replace("<", " "),
                        'dni': zoneDNI,
                        'cardNumber': zoneCardNumber,
                        'nation': zoneNation,
                        'traditional': False,
                        'passport': False,
                        'sex': zoneSex,
                        'endDate': datetime.stpftime(zoneOutDate, "yyMMdd"),
                        'birthday': datetime.stpftime(zoneBirthDate, "yyMMdd"),
                    })

                _logger.info("Verification Code: "
                             + verificationCode + " >> " + verCode)
            elif lines.length >= 3:
                # DNI Traditional
                zones = [
                    (0, 2),     # Tipo
                    (2, 5),     # Nacion
                    (5, 14),    # Numero DNI
                    (14, 15),   # Digito Control: Numero DNI

                    (0, 6),     # Fecha Nacimiento
                    (6, 7),     # Digito Control: Fecha Nacimiento
                    (7, 8),     # Sexo (M/F)
                    (8, 14),    # Fecha Caducidad
                    (14, 15),   # Digito Control: Fecha Caducidad
                    (15, 18),   # Nacionalidad
                    (29, 30),   # Digito Control Maestro

                    (0, 30),    # Nombre
                ]

                zoneDNI = lines[0][zones[2][0]:zones[2][1]]
                zoneDNIVer = lines[0][zones[3][0]:zones[3][1]]
                zoneBirthDate = lines[1][zones[4][0]:zones[4][1]]
                zoneBirthDateVer = lines[1][zones[5][0]:zones[5][1]]
                zoneSex = lines[1][zones[6][0]:zones[6][1]]
                zoneOutDate = lines[1][zones[7][0]:zones[7][1]]
                zoneOutDateVer = lines[1][zones[8][0]:zones[8][1]]
                zoneNation = lines[1][zones[9][0]:zones[9][1]]
                zoneName = lines[2][zones[11][0]:zones[11][1]]

                # Basic Info
                verificationCode = self._checkDigits(zoneDNI)
                verCode = int(zoneDNIVer)
                DNIReaded = (verificationCode == verCode) \
                    and self._isNifNie(zoneDNI)

                # Verify BirthDate
                verificationCode = self._checkDigits(zoneBirthDate)
                verCode = int(zoneBirthDateVer)
                DateBirthReaded = (verificationCode == verCode)

                # Verify OutDate
                verificationCode = self._checkDigits(zoneOutDate)
                verCode = int(zoneOutDateVer)
                OutDateReaded = (verificationCode == verCode)

                # Verify Sex
                SexReaded = zoneSex in possibleSexValues

                # Verify Master
                toVerify = zoneDNI + zoneDNIVer + zoneBirthDate \
                    + zoneBirthDateVer + zoneOutDate + zoneOutDateVer
                verificationCode = self._checkDigits(toVerify)
                verCode = int(lines[1][zones[10][0]:zones[10][1]])
                MasterVerificationReaded = (verificationCode == verCode)

                if DNIReaded and DateBirthReaded and OutDateReaded \
                        and MasterVerificationReaded and SexReaded:
                    result.update({
                        'result': recognizedText,
                        'name': zoneName.replace("<", " "),
                        'dni': zoneDNI,
                        'cardNumber': zoneCardNumber,
                        'nation': zoneNation,
                        'traditional': True,
                        'passport': False,
                        'sex': zoneSex,
                        'endDate': datetime.stpftime(zoneOutDate, "yyMMdd"),
                        'birthday': datetime.stpftime(zoneBirthDate, "yyMMdd"),
                    })

                _logger("Verification Code: " + verificationCode + " >> "
                        + verCode)
            else:
                # Pasaporte Electronico
                zones = [
                    (0, 1),     # Tipo
                    (2, 5),     # Nacion
                    (5, 43),    # Nombre

                    (0, 9),     # Num. Pasaporte
                    (9, 10),    # Digito Control: Num. Pasaporte
                    (10, 13),   # Nacionalidad
                    (13, 19),   # Fecha Nacimiento
                    (19, 20),   # Digito Control: Fecha Nacimiento
                    (20, 21),   # Sexo
                    (21, 27),   # Fecha Cadudidad
                    (27, 28),   # Digito Control: Fecha Caducidad
                    (28, 39),   # DNI Pasaporte
                    (42, 43),   # Digito Control: DNI
                    (43, 44),   # Digito Control Maestro
                ]

                zoneName = lines[0][zones[2][0]:zones[2][1]]
                zonePassportNum = lines[1][zones[3][0]:zones[3][1]]
                zonePassportNumVer = lines[1][zones[4][0]:zones[4][1]]
                zoneNation = lines[1][zones[5][0]:zones[5][1]]
                zoneBirthDate = lines[1][zones[6][0]:zones[6][1]]
                zoneBirthDateVer = lines[1][zones[7][0]:zones[7][1]]
                zoneSex = lines[1][zones[8][0]:zones[8][1]]
                zoneOutDate = lines[1][zones[9][0]:zones[9][1]]
                zoneOutDateVer = lines[1][zones[10][0]:zones[10][1]]
                zoneDNI = lines[1][zones[11][0]:zones[11][1]]
                zoneDNIVer = lines[1][zones[12][0]:zones[12][1]]
                zoneMasterVer = lines[1][zones[13][0]:zones[13][1]]

                # Verify Passport
                verificationCode = self._checkDigits(zonePassportNum)
                verCode = int(zonePassportNumVer)
                PassportReaded = (verificationCode == verCode)

                # Verify Birthday
                verificationCode = self._checkDigits(zoneBirthDate)
                verCode = int(zoneBirthDateVer)
                DateBirthReaded = (verificationCode == verCode)

                # Verify OutDate
                verificationCode = self._checkDigits(zoneOutDate)
                verCode = int(zoneOutDateVer)
                OutDateReaded = (verificationCode == verCode)

                # Verify DNI
                verificationCode = self._checkDigits(zoneDNI)
                verCode = int(zoneDNIVer)
                DNIReaded = (verificationCode == verCode)

                # Verify Sex
                SexReaded = zoneSex in possibleSexValues

                # Verify Master
                verificationCode = self._checkDigits(
                    zonePassportNum + zonePassportNumVer + zoneBirthDate
                    + zoneBirthDateVer + zoneOutDate + zoneOutDateVer
                    + zoneDNI + zoneDNIVer)
                verCode = int(zoneMasterVer)
                MasterVerificationReaded = (verificationCode == verCode)

                if PassportReaded and DateBirthReaded and OutDateReaded \
                        and DNIReaded and MasterVerificationReaded \
                        and SexReaded:

                    result.update({
                        'result': recognizedText,
                        'name': zoneName.replace("<", " "),
                        'dni': zoneDNI,
                        'cardNumber': zonePassportNum,
                        'nation': zoneNation,
                        'traditional': False,
                        'passport': True,
                        'sex': zoneSex,
                        'endDate': datetime.stpftime(zoneOutDate, "yyMMdd"),
                        'birthday': datetime.stpftime(zoneBirthDate, "yyMMdd"),
                    })
        except Exception as e:
            e.printStackTrace()

        return result
