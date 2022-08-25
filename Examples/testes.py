from datetime import datetime

dt_obj = datetime.strptime('01.01.2020 00:00:00,00',
                           '%d.%m.%Y %H:%M:%S,%f')
millisec = dt_obj.timestamp() * 1000

print(millisec)

print(datetime.fromtimestamp(round(438310*3600)))

from datetime import datetime

dt_obj = datetime.strptime('01.01.2020 00:00:00,00',
                           '%d.%m.%Y %H:%M:%S,%f')
millisec = dt_obj.timestamp() * 1000

print(round(157784760/3600))


1577847600 # segundos