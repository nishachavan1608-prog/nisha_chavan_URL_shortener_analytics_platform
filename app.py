from ipaddress import ip_address
from urllib import response

from flask import Flask, render_template, request, redirect, send_file, flash
import random
import string
import sqlite3
import csv   #to save all the data using a comma (comma separated values)
import io
import qrcode   #to get the qr of any url
import requests
from io import BytesIO
from datetime import datetime, timedelta
#to download the pdf
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
app = Flask(__name__)
app.secret_key="mysecretkey123"
#work for the actual work on the home page 
@app.route('/', methods=['GET', 'POST'])
def home():

    short_url = ""
    error = ""

    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    if request.method == "POST":

        entered_url = request.form.get("long_url", "").strip()
        custom_code = request.form.get("custom_code", "").strip()
        expiry_days = int(request.form.get("expiry_days", 30))

        if entered_url == "":
            error = "Please enter a URL."

        elif "." not in entered_url:
            error = "Please enter a valid URL."

        else:

            if not entered_url.startswith("http://") and not entered_url.startswith("https://"):
                entered_url = "https://" + entered_url

            if custom_code == "":
                generated_code = ''.join(
                    random.choices(string.ascii_letters + string.digits, k=6)
                )
            else:
                generated_code = custom_code

                cursor.execute(
                    "SELECT * FROM urls WHERE short_code=?",
                    (generated_code,)
                )

                if cursor.fetchone():
                    error = "Custom code already exists."

            if error == "":

                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                INSERT INTO urls
                (original_url, short_code, clicks, created_at, expiry_days)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entered_url,
                    generated_code,
                    0,
                    created_at,
                    expiry_days
                ))

                conn.commit()

                flash(request.host_url+generated_code)
                return redirect("/")

    # -------- Dashboard Statistics --------

    cursor.execute("SELECT COUNT(*) FROM urls")
    total_urls = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(clicks) FROM urls")
    total_clicks = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT original_url,
               short_code,
               clicks,
               created_at,
               expiry_days
        FROM urls
        ORDER BY id DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()

    data = []

    active_urls = 0
    expired_urls = 0
    today_urls = 0

    today = datetime.now().date()

    cursor.execute("""
        SELECT created_at, expiry_days
        FROM urls
    """)

    all_rows = cursor.fetchall()

    for created_at, expiry in all_rows:

        created_date = datetime.strptime(
            created_at,
            "%Y-%m-%d %H:%M:%S"
        )

        if created_date.date() == today:
            today_urls += 1

        expiry_date = created_date + timedelta(days=expiry)

        if datetime.now() > expiry_date:
            expired_urls += 1
        else:
            active_urls += 1

    for row in rows:

        created_date = datetime.strptime(
            row[3],
            "%Y-%m-%d %H:%M:%S"
        )

        expiry_date = created_date + timedelta(days=row[4])

        status = "Expired" if datetime.now() > expiry_date else "Active"

        data.append((
            row[0],
            row[1],
            row[2],
            status
        ))

    conn.close()
    from flask import get_flashed_messages
    messages=get_flashed_messages()
    if messages:
        short_url=messages[0]
    else:
        short_url="" 

    return render_template(
        "index.html",
        short_url=short_url,
        error=error,
        data=data,
        total_urls=total_urls,
        total_clicks=total_clicks,
        active_urls=active_urls,
        expired_urls=expired_urls,
        today_urls=today_urls
    )


#work for creating the short code
@app.route("/bulk_upload", methods=["POST"])
def bulk_upload():
    file = request.files.get("csv_file")

    if not file:
        flash("No CSV file selected.")
        return redirect("/")

    stream = io.StringIO(file.stream.read().decode("utf-8-sig"))
    csv_reader = csv.DictReader(stream)
    csv_reader.fieldnames = [name.strip().replace("\ufeff", "") for name in csv_reader.fieldnames]

    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    for row in csv_reader:
        print(row)

        entered_url = list(row.values())[0].strip()

        if entered_url == "":
            continue

        if not entered_url.startswith("http://") and not entered_url.startswith("https://"):
            entered_url = "https://" + entered_url

        generated_code = ''.join(
            random.choices(string.ascii_letters + string.digits, k=6)
        )

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO urls
            (original_url, short_code, clicks, created_at, expiry_days)
            VALUES (?, ?, ?, ?, ?)
        """, (
            entered_url,
            generated_code,
            0,
            created_at,
            30
        ))

    conn.commit()
    conn.close()

    flash("CSV uploaded successfully!")
    return redirect("/")
@app.route('/<short_code>')
def redirect_url(short_code):
        print("===============URL OPENED======================")
        print("SHORT CODE=",short_code)
        print("IP=",request.remote_addr)
        print("USER AGENT=",request.user_agent.string)
        if short_code=="favicon.ico":
            return "",204
        conn = sqlite3.connect("urls.db")
        cursor = conn.cursor()
        cursor.execute("""SELECT original_url,clicks, created_at, expiry_days FROM urls WHERE short_code=?""",(short_code,))
        result = cursor.fetchone()
        if result is None:
            conn.close()
            return render_template("expired.html")
        if result:
            
            original_url = result[0]
            current_clicks = result[1]
            created_at=result[2]
            expiry_days=result[3] if result[3] is not None else 30
            print("Url Opened :",short_code)
            print("User Agent:")
            created_date=datetime.strptime(created_at,"%Y-%m-%d %H:%M:%S")
            if datetime.now()>created_date+timedelta(days=expiry_days):
                cursor.execute("DELETE FROM urls WHERE short_code=?",(short_code,))
                conn.commit()
                conn.close()
                return render_template("expired.html")
            last_visit=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ip_address = request.headers.get("X-Forwarded-For")

            if ip_address:
                ip_address = ip_address.split(",")[0].strip()
            else:
              ip_address = request.remote_addr
            print("IP:", ip_address)
            country = "Unknown"
            city = "Unknown"
            try:
                response = requests.get(f"http://ip-api.com/json/{ip_address}? fields=status,country,city",timeout=5
    )

                location_data = response.json()
                print("Location Data:", location_data)

                if location_data.get("status") == "success":
                     country = location_data.get("country", "Unknown")
                     city = location_data.get("city", "Unknown")

            except Exception as e:
                print("Exception:", e)
                
            user_agent = request.user_agent.string
            print("USER AGENT=", request.user_agent.string)
            if "Android" in user_agent:
             device = "Android"
            elif "iPhone" in user_agent or "iPad" in user_agent:
             device = "iPhone"
            elif "Windows" in user_agent:
               device = "Windows"
            elif "Macintosh" in user_agent:
                device = "Mac"
            else:
             device = "Unknown"
            cursor.execute("""UPDATE urls SET clicks=?,last_visited=? WHERE short_code=?""",(current_clicks + 1,last_visit,short_code))
            cursor.execute("""INSERT INTO click_history(short_code, visit_time, device, ip_address, country, city)VALUES (?, ?, ?, ?, ?, ?)""",
            (short_code,last_visit,device,ip_address,country,city))
            conn.commit()
            conn.close()
            return redirect(original_url)
        conn.close()
        return "URL not found!"
#for the analytics page 
@app.route('/analytics')
def analytics():
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()
    cursor.execute("""SELECT original_url, short_code, clicks, created_at,last_visited, expiry_days FROM urls""")
    data = cursor.fetchall()
    #code for the auto delete url after the 2 days
    for row in data:
        created_at=row[3]
        expiry_days=row[5] if row[5] is not None else 30
        created_date=datetime.strptime(created_at,"%Y-%m-%d %H:%M:%S")
        expiry_date=created_date+timedelta(days=expiry_days)
        delete_date=expiry_date+timedelta(days=2)
        if datetime.now()>delete_date:
            cursor.execute("DELETE FROM urls WHERE short_code=?",(row[1],))
            cursor.execute("DELETE FROM click_history WHERE short_code=?",(row[1],))
    conn.commit()

    updated_data=[]

    for row in data:

        cursor.execute("""SELECT device, country, city, ip_address FROM click_history WHERE short_code=? AND country!='Unknown'ORDER BY id DESC LIMIT 1""", (row[1],))
        visit = cursor.fetchone()

        if visit:
            device = visit[0]
            country = visit[1]
            city = visit[2]
            ip_address = visit[3]
        else:
            device = "Unknown"
            country = "Unknown"
            city = "Unknown"
            ip_address = "Unknown"
        created_date = datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
        expiry_days = row[5] if row[5] is not None else 30

        expiry_date = created_date + timedelta(days=expiry_days)

        if datetime.now() > expiry_date:
           status = "Expired"
           days_left = "Expired"
        else:
         status = "Active"
         days_left = (expiry_date.date() - datetime.now().date()).days

         if days_left == 0:
            days_left = "Expires Today"

        updated_data.append(
    row + (
        device,
        status,
        days_left,
        country,
        city,
        ip_address
    )
)
    
    sorted_data=sorted(updated_data,key=lambda x:x[2],reverse=True)
    top_urls = sorted_data[:5]
    labels=[]
    click_values=[]
    for row in top_urls:
        labels.append(row[1])
        click_values.append(row[2])
    #to show the total no. of urls
    total_urls = len(data)
    total_clicks = 0
    for row in data:
        total_clicks+= row[2]
        #to display the most clicked url
    most_clicked_url="NO URLs yet "
    max_clicks=0
    for row in data:
        if row[2]>=max_clicks:
            max_clicks=row[2]
            most_clicked_url=row[0]
    #most clicked urls
    active_urls=0
    expired_urls=0
    for row in data:
        created_at=row[3]
        expiry_days=row[5]
        if expiry_days is None:
            active_urls+=1
        else:
            created_date=datetime.strptime(created_at,"%Y-%m-%d %H:%M:%S")
            if datetime.now() > created_date+timedelta(days=expiry_days):
                expired_urls+=1
            else:
                active_urls+=1
    cursor.execute("""SELECT short_code, visit_time,device FROM click_history ORDER BY id DESC LIMIT 10""")
    recent_visits=cursor.fetchall()
    print("Recent Visits=",recent_visits)
    today = datetime.now().strftime("%Y-%m-%d")

    today_urls = 0

    for row in data:
         if row[3].startswith(today):
             today_urls += 1
    print("Today's URLs=",today_urls)
    print("Rows from DS:",len(data))
    print("Rows sent to template:",len(updated_data))
    cursor.execute("""SELECT device, COUNT(*) FROM click_history GROUP BY device""")
    device_data=cursor.fetchall()
    device_labels=[]
    device_counts=[]
    for row in device_data:
        device_labels.append(row[0])
        device_counts.append(row[1])


    conn.close()
    return render_template("analytics.html", data=updated_data,total_urls=total_urls,total_clicks=total_clicks,active_urls=active_urls, expired_urls=expired_urls, most_clicked_url=most_clicked_url, max_clicks=max_clicks, labels=labels, click_values=click_values, top_urls=top_urls,recent_visits=recent_visits,today_urls=today_urls, device_labels=device_labels, device_counts=device_counts)
@app.route('/edit/<short_code>',methods=['GET','POST'])
def edit_url(short_code):
    conn=sqlite3.connect("urls.db")
    cursor=conn.cursor()
    if request.method=='POST':
        new_url=request.form['new_url']
        new_expiry=request.form['expiry_days']
        cursor.execute("UPDATE urls SET original_url=?,expiry_days=? WHERE short_code=?",(new_url,new_expiry,short_code))
        conn.commit()
        conn.close()
        return redirect('/analytics')
    cursor.execute("SELECT original_url, expiry_days FROM urls WHERE short_code=?",(short_code,))
    data=cursor.fetchone()
    conn.close()
    return render_template("edit.html",original_url=data[0],expiry_days=data[1],short_code=short_code)
    
#for the delete button inside the analytics
@app.route('/delete/<short_code>')
def delete_url(short_code):
    conn=sqlite3.connect("urls.db")
    cursor=conn.cursor()
    cursor.execute("DELETE FROM urls WHERE short_code=?",(short_code,))
    conn.commit()
    print("Deleted:",short_code)
    conn.close()
    return redirect('/analytics')
#to download the whole list of search
@app.route('/export')
def export_csv():
    conn=sqlite3.connect("urls.db")
    cursor=conn.cursor()
    cursor.execute("SELECT original_url, short_code, clicks, created_at FROM urls" )
    data=cursor.fetchall()
    conn.close()
    with open("analytics_report.csv","w",newline="") as file:
        writer=csv.writer(file)
        writer.writerow(["original URL","short Code","Clicks","Created At"])
        writer.writerows(data)
    return send_file("analytics_report.csv",as_attachment=True
        )
@app.route('/export_pdf')
def export_pdf():
    conn=sqlite3.connect("urls.db")
    cursor=conn.cursor()
    cursor.execute("SELECT original_url, short_code, clicks, created_at FROM urls")
    data=cursor.fetchall()
    conn.close()
    pdf=SimpleDocTemplate("analytics_report.pdf")
    styles=getSampleStyleSheet()
    content=[]
    content.append(Spacer(1,12))
    for row in data:
        url, code, clicks, created_at=row
        text=f"""URL:{url} | Code:{code} | clicks:{clicks} | created At:{created_at}"""

        content.append(Paragraph(text,styles['BodyText']))
        content.append(Spacer(1,8))
    pdf.build(content)
    return send_file("analytics_report.pdf",as_attachment=True, download_name="analytics_report.pdf")
#to add a qr code optin on the analytics page of the webpage
@app.route('/qr/<short_code>')
def generate_qr(short_code):
    short_url=request.host_url+short_code
    qr=qrcode.make(short_url)
    img_io=BytesIO()
    qr.save(img_io,'PNG')
    img_io.seek(0)
    return send_file(img_io,mimetype='image/png')
@app.route('/download_qr/<short_code>')
def download_qr(short_code):
    short_url=request.host_url+short_code
    qr=qrcode.make(short_url)
    img_io=BytesIO()
    qr.save(img_io,'PNG')
    img_io.seek(0)
    return send_file(img_io,mimetype='image/png',as_attachment=True,download_name=f"{short_code}_qr.png")
@app.route('/details/<short_code>')
def view_details(short_code):
    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT original_url, short_code, clicks, created_at,
               last_visited, expiry_days
        FROM urls
        WHERE short_code=?
    """, (short_code,))
    
    url_data = cursor.fetchone()
    cursor.execute("""
SELECT visit_time, device
FROM click_history
WHERE short_code=?
ORDER BY id DESC
""", (short_code,))
    
    
    visits = cursor.fetchall()
    print("Visits=",visits)
    labels=[]
    click_counts=[]
    for i,visit in enumerate(visits):
        labels.append(f"Visit {i+1}")
        click_counts.append(1)
    cursor.execute("""SELECT DATE(visit_time),COUNT(*) FROM click_history WHERE short_code=? GROUP BY DATE(visit_time) ORDER BY DATE(visit_time)""",(short_code,))
    chart_data=cursor.fetchall()
    chart_labels=[]
    chart_values=[]
    for row in chart_data:
        chart_labels.append(row[0])
        chart_values.append(row[1])


    conn.close()

    return render_template(
        "details.html",
        url_data=url_data,
        visits=visits,labels=labels,click_counts=click_counts,chart_labels=chart_labels,chart_values=chart_values )
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)