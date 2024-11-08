import os, smtplib, email, calendar, datetime, email.message, locale
from . import task

locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')

def get_week_of_month(data):
    first_day_of_month = data.replace(day=1)
    dom_first = first_day_of_month.weekday()
    adjusted_day = data.day + dom_first
    return (adjusted_day - 1) // 7 + 1

@task
async def main(*args, **kwargs):
    hoje = datetime.datetime.now()
    semana = get_week_of_month(hoje)
    nome_mes = hoje.strftime('%B')
    ano = datetime.datetime.now().year

    mail = email.message.EmailMessage()
    mail['From']    = 'tuper@noreply.com.br'
    mail['To']      = kwargs['mail']
    mail['Subject'] = 'Relatório semanal'
    mail.set_content(f"Olá {kwargs['name']}, segue em anexo seu relatório da {semana}ª semana de {nome_mes} de {ano}.")

    with open(kwargs['attachment'], 'rb') as f:
        filename = kwargs['attachment'].split('\\')[-1]
        mail.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=filename)

    with smtplib.SMTP('mail', 25) as smtp:
        smtp.send_message(mail)
    print("E-mail enviado com sucesso!")