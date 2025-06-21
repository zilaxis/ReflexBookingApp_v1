from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from fastapi.responses import FileResponse
from fastapi.responses import Response

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

import json
import os

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BOOKING_FILE = "bookings.json"

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("booking_form.html", {"request": request})

@app.post("/add_booking")
def add_booking(
    request: Request,
    name: str = Form(...),
    service: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    quantity: int = Form(...),
):
    booking = {
        "name": name,
        "service": service,
        "date": date,
        "time": time,
        "quantity": quantity,
    }

    bookings = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            bookings = json.load(f)

    bookings.append(booking)

    with open(BOOKING_FILE, "w", encoding="utf-8") as f:
        json.dump(bookings, f, ensure_ascii=False, indent=4)

    request.session["flash"] = "จองตั๋วสำเร็จแล้ว!"
    return RedirectResponse(url="/bookings", status_code=303)

@app.get("/bookings", response_class=HTMLResponse)
def view_bookings(request: Request, search: str = ""):
    bookings = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            bookings = json.load(f)

    if search:
        bookings = [b for b in bookings if search.lower() in b["name"].lower() or search.lower() in b["service"].lower()]

    flash_message = request.session.pop("flash", None)

    return templates.TemplateResponse("bookings.html", {
        "request": request,
        "bookings": bookings,
        "message": flash_message
    })

@app.get("/delete/{index}")
def delete_booking(index: int, request: Request):
    bookings = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            bookings = json.load(f)

    if 0 <= index < len(bookings):
        bookings.pop(index)

        with open(BOOKING_FILE, "w", encoding="utf-8") as f:
            json.dump(bookings, f, ensure_ascii=False, indent=4)

        request.session["flash"] = "ลบรายการเรียบร้อยแล้ว"

    return RedirectResponse(url="/bookings", status_code=303)

@app.post("/edit/{index}")
def edit_booking(index: int, request: Request,
                 name: str = Form(...),
                 service: str = Form(...),
                 date: str = Form(...),
                 time: str = Form(...),
                 quantity: int = Form(...)):
    bookings = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            bookings = json.load(f)

    if 0 <= index < len(bookings):
        bookings[index] = {
            "name": name,
            "service": service,
            "date": date,
            "time": time,
            "quantity": quantity,
        }

        with open(BOOKING_FILE, "w", encoding="utf-8") as f:
            json.dump(bookings, f, ensure_ascii=False, indent=4)

        request.session["flash"] = "แก้ไขข้อมูลสำเร็จแล้ว!"

    return RedirectResponse(url="/bookings", status_code=303)

@app.get("/edit/{index}", response_class=HTMLResponse)
def edit_page(index: int, request: Request):
    bookings = []
    if os.path.exists(BOOKING_FILE):
        with open(BOOKING_FILE, "r", encoding="utf-8") as f:
            bookings = json.load(f)

    booking = bookings[index] if 0 <= index < len(bookings) else None

    return templates.TemplateResponse("edit.html", {
        "request": request,
        "index": index,
        "booking": booking
    })

@app.get("/export/pdf")
def export_pdf():
    file_path = "bookings.json"
    if not os.path.exists(file_path):
        return {"error": "ไม่พบไฟล์ข้อมูล"}

    with open(file_path, "r", encoding="utf-8") as f:
        bookings = json.load(f)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    data = [["ชื่อ", "บริการ", "วันที่", "เวลา", "จำนวนที่นั่ง"]]
    for b in bookings:
        data.append([
            b.get("name", ""),
            b.get("service", ""),
            b.get("date", ""),
            b.get("time", ""),
            str(b.get("quantity", ""))
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 12),
    ]))

    doc.build([table])
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=bookings.pdf"
    })