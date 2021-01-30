import smtplib


server = smtplib.SMTP('smtp.gmail.com', 25)
server.connect("smtp.gmail.com",587)
server.starttls()
server.login('datapotatoinc@gmail.com', 'vtbdata4567Q!')
server.sendmail('datapotatoinc@gmail.com', 'bagirov.ramil@gmail.com', 'test')
server.quit()