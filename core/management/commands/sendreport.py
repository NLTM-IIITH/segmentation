import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pprint import pprint

from django.core.management.base import BaseCommand
from django.db.models import Count, F, Q, Sum, Value
from django.db.models.functions import Concat, Lower

from page.models import Page


def send_mail(email, content, total):

  message = MIMEMultipart("alternative")
  message["Subject"] = "[Segmentation] Report as on {}".format(date.today().strftime('%d-%m-%Y'))
  message["From"] = 'Data Admin <kt.krishna.tulsyan@gmail.com>'
  message["To"] = email

  # write the text/plain part
  text = """\
  Hi,
  This email contains the daily report on the Data platform.
  If you are not able to view any table, please reply back stating the same."""

  html = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
  <head>
    <!-- Compiled with Bootstrap Email version: 1.4.0 --><meta http-equiv="x-ua-compatible" content="ie=edge">
    <meta name="x-apple-disable-message-reformatting">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="format-detection" content="telephone=no, date=no, address=no, email=no">
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style type="text/css">
      body,table,td{font-family:Helvetica,Arial,sans-serif !important}.ExternalClass{width:100%}.ExternalClass,.ExternalClass p,.ExternalClass span,.ExternalClass font,.ExternalClass td,.ExternalClass div{line-height:150%}a{text-decoration:none}*{color:inherit}a[x-apple-data-detectors],u+#body a,#MessageViewBody a{color:inherit;text-decoration:none;font-size:inherit;font-family:inherit;font-weight:inherit;line-height:inherit}img{-ms-interpolation-mode:bicubic}table:not([class^=s-]){font-family:Helvetica,Arial,sans-serif;mso-table-lspace:0pt;mso-table-rspace:0pt;border-spacing:0px;border-collapse:collapse}table:not([class^=s-]) td{border-spacing:0px;border-collapse:collapse}@media screen and (max-width: 600px){.w-full,.w-full>tbody>tr>td{width:100% !important}*[class*=s-lg-]>tbody>tr>td{font-size:0 !important;line-height:0 !important;height:0 !important}.s-2>tbody>tr>td{font-size:8px !important;line-height:8px !important;height:8px !important}.s-5>tbody>tr>td{font-size:20px !important;line-height:20px !important;height:20px !important}.s-10>tbody>tr>td{font-size:40px !important;line-height:40px !important;height:40px !important}}
    </style>
  </head>
  <body class="bg-light" style="outline: 0; width: 100%; min-width: 100%; height: 100%; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, sans-serif; line-height: 24px; font-weight: normal; font-size: 16px; -moz-box-sizing: border-box; -webkit-box-sizing: border-box; box-sizing: border-box; color: #000000; margin: 0; padding: 0; border-width: 0;" bgcolor="#f7fafc">
    <table class="bg-light body" valign="top" role="presentation" border="0" cellpadding="0" cellspacing="0" style="outline: 0; width: 100%; min-width: 100%; height: 100%; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-family: Helvetica, Arial, sans-serif; line-height: 24px; font-weight: normal; font-size: 16px; -moz-box-sizing: border-box; -webkit-box-sizing: border-box; box-sizing: border-box; color: #000000; margin: 0; padding: 0; border-width: 0;" bgcolor="#f7fafc">
      <tbody>
        <tr>
          <td valign="top" style="line-height: 24px; font-size: 16px; margin: 0;" align="left" bgcolor="#f7fafc">
            <table class="container-fluid" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;">
              <tbody>
                <tr>
                  <td style="line-height: 24px; font-size: 16px; width: 100%; margin: 0; padding: 0 16px;" align="left">
                    <table class="s-10 w-full" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;" width="100%">
                      <tbody>
                        <tr>
                          <td style="line-height: 40px; font-size: 40px; width: 100%; height: 40px; margin: 0;" align="left" width="100%" height="40">
                            &#160;
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <table class="card" role="presentation" border="0" cellpadding="0" cellspacing="0" style="border-radius: 6px; border-collapse: separate !important; width: 100%; overflow: hidden; border: 1px solid #e2e8f0;" bgcolor="#ffffff">
                      <tbody>
                        <tr>
                          <td style="line-height: 24px; font-size: 16px; width: 100%; margin: 0;" align="left" bgcolor="#ffffff">
                            <table class="card-body" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;">
                              <tbody>
                                <tr>
                                  <td style="line-height: 24px; font-size: 16px; width: 100%; margin: 0; padding: 20px;" align="left">
                                    <h1 class="h3  text-center" style="padding-top: 0; padding-bottom: 0; font-weight: 500; vertical-align: baseline; font-size: 28px; line-height: 33.6px; margin: 0;" align="center">Segmentation Data Report (""" + str(date.today().strftime('%d-%m-%Y')) + """)</h1>
                                    <table class="s-2 w-full" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;" width="100%">
                                      <tbody>
                                        <tr>
                                          <td style="line-height: 8px; font-size: 8px; width: 100%; height: 8px; margin: 0;" align="left" width="100%" height="8">
                                            &#160;
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                    <table class="s-5 w-full" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;" width="100%">
                                      <tbody>
                                        <tr>
                                          <td style="line-height: 20px; font-size: 20px; width: 100%; height: 20px; margin: 0;" align="left" width="100%" height="20">
                                            &#160;
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                    <table class="hr" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;">
                                      <tbody>
                                        <tr>
                                          <td style="line-height: 24px; font-size: 16px; border-top-width: 1px; border-top-color: #e2e8f0; border-top-style: solid; height: 1px; width: 100%; margin: 0;" align="left">
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                    <table class="s-5 w-full" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;" width="100%">
                                      <tbody>
                                        <tr>
                                          <td style="line-height: 20px; font-size: 20px; width: 100%; height: 20px; margin: 0;" align="left" width="100%" height="20">
                                            &#160;
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                    <table class="table table-bordered text-center" border="0" cellpadding="0" cellspacing="0" style="width: 100%; max-width: 100%; text-align: center !important; border: 1px solid #e2e8f0;">
                                      <thead>
                                        <tr>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Modality</th>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Language</th>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Unassigned Pages</th>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Assigned Pages</th>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Completed Pages</th>
                                          <th style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border-color: #e2e8f0; border-style: solid; border-width: 1px 1px 2px;" align="left" valign="top">Skipped Pages</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        <tr style="font-weight: bold; background-color: #c5e1a5;">
                                          <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top" colspan="2">Total</td>
                                          <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">"""+str(total['sum_pending'])+"""</td>
                                          <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">"""+str(total['sum_assigned'])+"""</td>
                                          <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">"""+str(total['sum_corrected'])+"""</td>
                                          <td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">"""+str(total['sum_skipped'])+"""</td>
                                        </tr>
                    """ + content + """
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                    <table class="s-10 w-full" role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%;" width="100%">
                      <tbody>
                        <tr>
                          <td style="line-height: 40px; font-size: 40px; width: 100%; height: 40px; margin: 0;" align="left" width="100%" height="40">
                            &#160;
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
          </td>
        </tr>
      </tbody>
    </table>
  </body>
</html>"""


  # convert both parts to MIMEText objects and add them to the MIMEMultipart message
  part1 = MIMEText(text, "plain")
  part2 = MIMEText(html, "html")
  message.attach(part1)
  message.attach(part2)

  s = smtplib.SMTP('smtp.gmail.com', 587)
  s.starttls()
  s.login('kt.krishna.tulsyan@gmail.com', 'ahqqznyhleeszlez')
  s.sendmail('kt.krishna.tulsyan@gmail.com', email, message.as_string())
  s.quit()

class Command(BaseCommand):
  help = "Sends all the available verified jobs to the segmentation portal"

  def handle(self, *args, **kwargs):
    pages = Page.objects.all()
    pages = pages.annotate(
      model=Concat(
        Lower(F('category')),
        Value(' '),
        Lower(F('language')),
      )
    )



    pages = pages.values('model').annotate(
      pending=Count('id', filter=Q(status__in=('new', 'segmented'))),
      assigned=Count('id', filter=Q(status='assigned')),
      corrected=Count('id', filter=Q(status='corrected')),
      skipped=Count('id', filter=Q(status='skip')),
    )
    total = pages.aggregate(
      sum_pending=Sum('pending'),
      sum_assigned=Sum('assigned'),
      sum_corrected=Sum('corrected'),
      sum_skipped=Sum('skipped'),
    )
    pages = sorted(
      list(pages),
      key=lambda x:(-ord(x['model'].split(' ')[0][0]), x['model'].split(' ')[-1][0])
    )
    pprint(pages)
    pprint(total)

    out = []
    for i in pages:
      x = ''.join((
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["model"].split(" ")[0].title()}</td>',
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["model"].split(" ")[1].title()}</td>',
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["pending"]}</td>',
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["assigned"]}</td>',
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["corrected"]}</td>',
        f'<td style="line-height: 24px; font-size: 16px; margin: 0; padding: 12px; border: 1px solid #e2e8f0;" align="center" valign="top">{i["skipped"]}</td>',
      ))
      out.append(f'<tr>{x}</tr>')
    send_mail('krishna.tulsyan@research.iiit.ac.in', ''.join(out), total)
    send_mail('ajoy.mondal@iiit.ac.in', ''.join(out), total)
    send_mail('aradhana.vinod@research.iiit.ac.in', ''.join(out), total)
    send_mail('jawahar@iiit.ac.in', ''.join(out), total)
    send_mail('gs.lehal@research.iiit.ac.in', ''.join(out), total)
    send_mail('ram.sharma@research.iiit.ac.in', ''.join(out), total)
    self.stdout.write(
      self.style.SUCCESS(f'Sent Data Segmentation email to all receiptients')
    )