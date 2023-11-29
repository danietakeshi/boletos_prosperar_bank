import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from premailer import transform
from dotenv import load_dotenv
import os

load_dotenv()

# Replace these variables with your email credentials and settings
sender_email = os.environ.get("SENDER_EMAIL")
sender_password = os.environ.get("SENDER_PASS")
recipient_email = 'martins.takeshi@gmail.com'
smtp_server = os.environ.get("SMTP_SERVER")
smtp_port = os.environ.get("SMTP_PORT")

# Carregando os Lançamentos
def gerar_tabela_completa(filename: str = 'backup_granatum.csv') -> pd.DataFrame:
    # Lendo CSV de Lançamentos do Granatum
    df = pd.read_csv(f'../update/{filename}', encoding='latin-1', sep=';')

    # Selecionando somente o tipo de pagamento e excluindo o cliente Granatum
    df = df[((df['Forma de pagamento'] == 'Boleto - Granatum Pagamentos') | (df['Forma de pagamento'] == 'Boleto ProsperarBank')) & (df['Cliente/Fornecedor'] != 'GRANATUM LTDA - EPP')]
    
    # Alterando o valor do boletos para R$ 4,50
    df.loc[df['Categoria'] == '005 - Tx Boleto', 'Valor'] = '4,50'
    
    # Remove o boleto da C. Beatriz
    df = df[df['Cliente/Fornecedor'] != 'BEATRIZ DA ROSA']

    # Selecionando as colunas necessárias
    df = df[['Cliente/Fornecedor', 'Data de vencimento', 'Descrição', 'Valor', 'Documento cliente/fornecedor']]

    # Colocando todos os Vencimentos no dia 10
    df['Data de vencimento'] = '10' + df['Data de vencimento'].str[2:]

    # Lendo Lista de Sócios
    df_socios = pd.read_parquet(f'../socios/lista_de_socios.parquet')

    # Unindo as informações das Tabelas de Lançamentos e de Sócios
    df_complete = pd.merge(
        df,
        df_socios,
        how="inner",
        left_on="Cliente/Fornecedor",
        right_on="Nome/Razão Social",
        suffixes=("_x", "_y"),
        copy=True,
        indicator=False,
        validate=None,
    )
    
    # Transforma a coluna de Valor em Float
    df_complete['Valor'] = df_complete['Valor'].str.replace(',','.').astype(float)
    
    # Filtrando as Colunas necessárias
    df_complete = df_complete[['Cliente/Fornecedor', 'Data de vencimento', 'Descrição', 'Valor', 'Email']]
    
    # Renomeando as colunas
    df_complete = df_complete.rename(columns={
        'Data de vencimento' : 'Vencimento',
        'Cliente/Fornecedor' : 'Nome',
        })
    
    return df_complete

# Function to format expenses data into an HTML table with style
def format_expenses_table(df):
    styled_table = df.style.format({
        'Valor': '{:,.2f}'.format
    }).set_table_styles([
        {'selector': 'th',
         'props': [('border-bottom', '1px solid #dddddd'), ('text-align', 'right'),
                   ('padding', '8px')]},
        {'selector': 'td',
         'props': [('border-bottom', '1px solid #dddddd'), ('text-align', 'right'),
                   ('padding', '8px')]},
        {'selector': 'td:first-child',
         'props': [('text-align', 'left')]},
        {'selector': 'th:first-child',
         'props': [('text-align', 'left')]}
    ]).hide(axis="index").to_html()

    return transform(styled_table)

def generate_mailing(df: pd.DataFrame, test: bool = False) -> str:
  # Get formatted expenses table
  expenses_table = format_expenses_table(df[['Descrição', 'Valor']])

  overall_total = df['Valor'].sum()
  overall_total_row = f'<tr><td align="left" style="padding: 8px"><b>Valor Total:</b></td><td align="right" style="padding: 8px">{overall_total:.2f}</td></tr>'

  # Create the HTML content for the email
  html_content = '''
  <!doctype html>
  <html>
    <head>
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
      <title>Simple Transactional Email</title>
      <style>
        /* -------------------------------------
            GLOBAL RESETS
        ------------------------------------- */
        
        /*All the styling goes here*/
        
        img {
          border: none;
          -ms-interpolation-mode: bicubic;
          max-width: 100%; 
        }

        body {
          background-color: #f6f6f6;
          font-family: sans-serif;
          -webkit-font-smoothing: antialiased;
          font-size: 14px;
          line-height: 1.4;
          margin: 0;
          padding: 0;
          -ms-text-size-adjust: 100%;
          -webkit-text-size-adjust: 100%; 
        }

        table {
          border-collapse: collapse;
          mso-table-lspace: 0pt;
          mso-table-rspace: 0pt;
          width: 100%; }
          table td {
            font-family: sans-serif;
            font-size: 14px;
            vertical-align: top; 
        }

        /* -------------------------------------
            BODY & CONTAINER
        ------------------------------------- */

        .body {
          background-color: #f6f6f6;
          width: 100%; 
        }

        /* Set a max-width, and make it display as block so it will automatically stretch to that width, but will also shrink down on a phone or something */
        .container {
          display: block;
          margin: 0 auto !important;
          /* makes it centered */
          max-width: 580px;
          padding: 10px;
          width: 580px; 
        }

        /* This should also be a block element, so that it will fill 100% of the .container */
        .content {
          box-sizing: border-box;
          display: block;
          margin: 0 auto;
          max-width: 580px;
          padding: 10px; 
        }

        /* -------------------------------------
            HEADER, FOOTER, MAIN
        ------------------------------------- */
        .main {
          background: #ffffff;
          border-radius: 3px;
          width: 100%; 
        }

        .wrapper {
          box-sizing: border-box;
          padding: 20px; 
        }

        .content-block {
          padding-bottom: 10px;
          padding-top: 10px;
        }

        .footer {
          clear: both;
          margin-top: 10px;
          text-align: center;
          width: 100%; 
        }
          .footer td,
          .footer p,
          .footer span,
          .footer a {
            color: #999999;
            font-size: 12px;
            text-align: center; 
        }

        /* -------------------------------------
            TYPOGRAPHY
        ------------------------------------- */
        h1,
        h2,
        h3,
        h4 {
          color: #000000;
          font-family: sans-serif;
          font-weight: 400;
          line-height: 1.4;
          margin: 0;
          margin-bottom: 30px; 
        }

        h1 {
          font-size: 35px;
          font-weight: 300;
          text-align: center;
          text-transform: capitalize; 
        }

        p,
        ul,
        ol {
          font-family: sans-serif;
          font-size: 14px;
          font-weight: normal;
          margin: 0;
          margin-bottom: 15px; 
        }
          p li,
          ul li,
          ol li {
            list-style-position: inside;
            margin-left: 5px; 
        }

        a {
          color: #3498db;
          text-decoration: underline; 
        }

        /* -------------------------------------
            BUTTONS
        ------------------------------------- */
        .btn {
          box-sizing: border-box;
          width: 100%; }
          .btn > tbody > tr > td {
            padding-bottom: 15px; }
          .btn table {
            width: auto; 
        }
          .btn table td {
            background-color: #ffffff;
            border-radius: 5px;
            text-align: center; 
        }
          .btn a {
            background-color: #ffffff;
            border: solid 1px #3498db;
            border-radius: 5px;
            box-sizing: border-box;
            color: #3498db;
            cursor: pointer;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
            margin: 0;
            padding: 12px 25px;
            text-decoration: none;
            text-transform: capitalize; 
        }

        .btn-primary table td {
          background-color: #3498db; 
        }

        .btn-primary a {
          background-color: #3498db;
          border-color: #3498db;
          color: #ffffff; 
        }

        /* -------------------------------------
            OTHER STYLES THAT MIGHT BE USEFUL
        ------------------------------------- */
        .last {
          margin-bottom: 0; 
        }

        .first {
          margin-top: 0; 
        }

        .align-center {
          text-align: center; 
        }

        .align-right {
          text-align: right; 
        }

        .align-left {
          text-align: left; 
        }

        .clear {
          clear: both; 
        }

        .mt0 {
          margin-top: 0; 
        }

        .mb0 {
          margin-bottom: 0; 
        }

        .preheader {
          color: transparent;
          display: none;
          height: 0;
          max-height: 0;
          max-width: 0;
          opacity: 0;
          overflow: hidden;
          mso-hide: all;
          visibility: hidden;
          width: 0; 
        }

        .powered-by a {
          text-decoration: none; 
        }

        hr {
          border: 0;
          border-bottom: 1px solid #f6f6f6;
          margin: 20px 0; 
        }

        /* -------------------------------------
            RESPONSIVE AND MOBILE FRIENDLY STYLES
        ------------------------------------- */
        @media only screen and (max-width: 620px) {
          table.body h1 {
            font-size: 28px !important;
            margin-bottom: 10px !important; 
          }
          table.body p,
          table.body ul,
          table.body ol,
          table.body td,
          table.body span,
          table.body a {
            font-size: 16px !important; 
          }
          table.body .wrapper,
          table.body .article {
            padding: 10px !important; 
          }
          table.body .content {
            padding: 0 !important; 
          }
          table.body .container {
            padding: 0 !important;
            width: 100% !important; 
          }
          table.body .main {
            border-left-width: 0 !important;
            border-radius: 0 !important;
            border-right-width: 0 !important; 
          }
          table.body .btn table {
            width: 100% !important; 
          }
          table.body .btn a {
            width: 100% !important; 
          }
          table.body .img-responsive {
            height: auto !important;
            max-width: 100% !important;
            width: auto !important; 
          }
        }

        /* -------------------------------------
            PRESERVE THESE STYLES IN THE HEAD
        ------------------------------------- */
        @media all {
          .ExternalClass {
            width: 100%; 
          }
          .ExternalClass,
          .ExternalClass p,
          .ExternalClass span,
          .ExternalClass font,
          .ExternalClass td,
          .ExternalClass div {
            line-height: 100%; 
          }
          .apple-link a {
            color: inherit !important;
            font-family: inherit !important;
            font-size: inherit !important;
            font-weight: inherit !important;
            line-height: inherit !important;
            text-decoration: none !important; 
          }
          #MessageViewBody a {
            color: inherit;
            text-decoration: none;
            font-size: inherit;
            font-family: inherit;
            font-weight: inherit;
            line-height: inherit;
          }
          .btn-primary table td:hover {
            background-color: #34495e !important; 
          }
          .btn-primary a:hover {
            background-color: #34495e !important;
            border-color: #34495e !important; 
          } 
        }

      </style>
    </head>
    <body>
      <span class="preheader">Lembrete de Mensalidade</span>
      <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body">
        <tr>
          <td>&nbsp;</td>
          <td class="container">
            <div class="content">

              <!-- START CENTERED WHITE CONTAINER -->
              <table role="presentation" class="main">

                <!-- START MAIN CONTENT AREA -->
                <tr>
                  <td class="wrapper">
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="background-color: #3498db;">
                      <tr>
                        <td style="text-align: center;"><img src="https://udv.org.br/wp-content/uploads/2016/01/centro-espirita-beneficente-uniao-do-vegetal-300x164.png" alt="UDV" style="display: block; margin: 0 auto;"></td>
                      </tr>
                    </table>
                    <br>
                    <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td>
                          <p>Olá, <b>''' + df.Nome.values[0].title() + '''!</b></p>
                          <p>Este é um aviso automático de cobrança emitido por <b>CEBUDV NSJB</b>, com vencimento em ''' + df.Vencimento.values[0] + '''</p>
                          ''' + expenses_table + '''<table>''' + overall_total_row + '''
                            </table>
                          <br>
                          <p>Fique de olho para não perder a data de vencimento!</p>
                          <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="btn btn-primary">
                            <tbody>
                              <tr>
                                <td align="left">
                                  <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                    <tbody>
                                      <tr>
                                        <td> <a href="https://sales.prosperarbank.secure.srv.br/billet/checkout/58d5e823-0eeb-4a15-832f-11de57c2b901" target="_blank">Visualizar Boleto</a> </td>
                                      </tr>
                                    </tbody>
                                  </table>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                          <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                          <tr>
                            <td>
                              <br>
                              <p>Use este código de barras para pagamentos no bankline:</p>
                              <p>34191.09008 07085.650393 32500.060002 9 94690000059660</p>
                              <br>
                              <p>Em caso de dúvidas entre em contato.</p>
                              <br>
                              <p>Atenciosamente,</p>
                              <p><b>Tesouraria NSJB</b></p>
                          </td></tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>

              <!-- END MAIN CONTENT AREA -->
              </table>
              <!-- END CENTERED WHITE CONTAINER -->

              <!-- START FOOTER -->
              <div class="footer">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                  <tr>
                    <td class="content-block">
                      <span class="apple-link">Estrada João Mineiro, 3303 Bairro São Pedro, Mairiporã SP 07613-800</span>
                    </td>
                  </tr>
                  <tr>
                    <td class="content-block powered-by">
                      Powered by <a href="https://i.pinimg.com/originals/82/6a/97/826a97bc3c85f06999008eafa4097c0a.gif">Senhor Barriga</a>.
                    </td>
                  </tr>
                </table>
              </div>
              <!-- END FOOTER -->

            </div>
          </td>
          <td>&nbsp;</td>
        </tr>
      </table>
    </body>
  </html>
  '''

  if test:
    with open(f'./teste_{df.Nome.values[0]}.html', 'w', encoding="utf-8") as f:
        f.write(html_content)

  return html_content, overall_total

def send_mail(recipient_email: str, html_content: str, valor_total: float) -> None:
  # Create the email message
  msg = MIMEMultipart()
  msg['From'] = sender_email
  msg['To'] = recipient_email
  msg['Subject'] = f'CEBUDV NSJB - Lembrete de Mensalidade: R$ {valor_total:.2f}'

  # Attach the HTML content to the email
  msg.attach(MIMEText(html_content, 'html'))

  # Connect to SMTP server and send the email
  try:
      server = smtplib.SMTP(smtp_server, smtp_port)
      server.starttls()
      server.login(sender_email, sender_password)
      server.sendmail(sender_email, recipient_email, msg.as_string())
      server.quit()
      print("Email sent successfully!")
  except Exception as e:
      print("Failed to send email.")
      print(e)


if __name__ == '__main__':
  df = gerar_tabela_completa('backup_granatum_20231129.csv')
  for socio in df.Nome.unique():
    if socio == 'DANIEL TAKESHI MARTINS':
      filter_df = df[df.Nome == socio]
      print(f"Encaminhando descritivo para {socio} com o valor de R$ {filter_df.Valor.sum():.02f}")
      #  print(filter_df)
      html_content, valor_total = generate_mailing(filter_df, test=True)
      send_mail(filter_df.Email.values[0], html_content, valor_total)


