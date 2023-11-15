from oauth2client.service_account import ServiceAccountCredentials
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import gspread
import json
import telebot
from datetime import datetime
bot = telebot.TeleBot('6584622284:AAFte6DgvrBK8jxj0WNMqmXlPt5sx6I5XcE')
TelegramUsers = [6521303025, 5105886481]

allow_anonymous = True;
record_dict = {}
months_dict = {"01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun", "07": "Jul", "08": "Aug", "09": "Sept", "10": "Oct", "11": "Nov", "12": "Dec"}

#Google Sheet Authentication
scopes = [
'https://www.googleapis.com/auth/spreadsheets',
'https://www.googleapis.com/auth/drive'
]
credentials = ServiceAccountCredentials.from_json_keyfile_name("gspread-credentials.json", scopes) #access the json key you downloaded earlier 
client = gspread.authorize(credentials) # authenticate the JSON key with gspread

def get_user_sheet(user):
    sample_spreadsheet = client.open('Expense Tracker');    
    spreadsheet_name = 'Expense Tracker_{}_{} {}'.format(user.id, user.first_name, user.last_name);
    spreadsheet_list = client.openall(spreadsheet_name);
    spreadsheet = client.copy(sample_spreadsheet.id, spreadsheet_name, True) if spreadsheet_list == [] else spreadsheet_list[0];
    client.insert_permission(spreadsheet.id, None, 'anyone', 'reader')
    return spreadsheet;


#Get today's date in integer format
def today_date():
    # Creating a datetime object so we can test.
    a = datetime.now()
    # Converting a to string in the desired format (YYYYMMDD) using strftime
    # and then to int.
    a = str(a.strftime('%d/%m/%y'))
    return a

#Checks if User is Authorized or not
def user_check(message):
    user = message.from_user
    if (user.id in TelegramUsers) or allow_anonymous == True:
        record_dict["User"] = user
        record_dict["CurrentSpreadSheet"] = get_user_sheet(user)
        return True
    else:
        bot.reply_to(message, "Unauthorized User")
        print(message.from_user.id)
        return False

#determine if money in or out
def start(message):
    start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_markup.row('Ăn uống', 'Di chuyển', 'Sách vở', 'Nhà ở')
    start_markup.row('Mua sắm online', 'Sức khoẻ' , 'Giải Trí', 'Vay mượn')
    sent = bot.send_message(message.chat.id, "Chọn danh mục tiêu dùng", reply_markup=start_markup)
    bot.register_next_step_handler(sent,get_category)

#get category data    
def get_category(message):
    category = message.text
    record_dict["Category"] = category

    start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    start_markup.row('Today')
    sent = bot.send_message(message.chat.id, "Ngày chi? (in dd/mm/yy)", reply_markup=start_markup)
    bot.register_next_step_handler(sent,get_date)

#get date data
def get_date(message):
    if message.text == 'Today':
        datee = today_date()
        record_dict["Date"] = datee
    else:
        datee = message.text
        record_dict["Date"] = datee
    sent = bot.send_message(message.chat.id,"Số tiền chi?")
    bot.register_next_step_handler(sent,get_amt)

def get_amt(message):
    amt = message.text
    record_dict["Amount"]=amt
    sent = bot.send_message(message.chat.id,"Mô tả chi tiết?")
    bot.register_next_step_handler(sent,get_description)

def get_description(message):
    desc = message.text
    record_dict["Description"]=desc
    bot.send_message(message.chat.id,"Updating...")
    update_sheet(message)

#Convert Date from dictionary to month as a string
def month_check():
    x = list(record_dict["Date"])
    x = x[-5:-3]
    y = ''.join(x)
    return y

def get_current_month():
    x = list(today_date())
    x = x[-5:-3]
    y = ''.join(x)
    return months_dict[y];

#Function to upload data to google sheets
def upload_data(worksheet,cell):
        cell_row = cell.row + 1
        cell_col = cell.col
        cell_val = worksheet.cell(cell_row, cell_col).value
        while cell_val is not None:
            cell_row = cell_row + 1
            print(cell_row)
            cell_val = worksheet.cell(cell_row, cell_col).value
        worksheet.update_cell(cell_row, cell_col, record_dict['Category'])
        worksheet.update_cell(cell_row,cell_col-1,record_dict['Description'])
        worksheet.update_cell(cell_row,cell_col-2,record_dict['Amount'])
        worksheet.update_cell(cell_row,cell_col-3,record_dict['Date'])

def update_sheet(message):
    user_spreadsheet = record_dict["CurrentSpreadSheet"]
    worksheet = user_spreadsheet.worksheet("Transactions") # get Transactions worksheet of the Spreadsheet
    cell = worksheet.find("Chi tiêu")
    upload_data(worksheet,cell)
    mthcheck = month_check()
    for x in months_dict:
        if x == mthcheck:
            worksheet = user_spreadsheet.worksheet(months_dict[x])
            cell = worksheet.find("Chi tiêu")
            upload_data(worksheet,cell)
            print("Data Uploaded to {} worksheet.".format(months_dict[x]))
            break
        else:
            continue
    bot.send_message(message.chat.id,"Updated")    


def get_report():
    if record_dict["User"] is not None:
        report_data = {}
        
        month_worksheet = record_dict["CurrentSpreadSheet"].worksheet(get_current_month())
        month_label_cell = month_worksheet.find("Tổng chi:")
        report_data["MonthExpenses"] = month_worksheet.cell(month_label_cell.row, month_label_cell.col + 1).value
        
        ts_worksheet = record_dict["CurrentSpreadSheet"].worksheet('Transactions')
        ts_label_cell = ts_worksheet.find("Tổng chi:")
        report_data["TotalExpenses"] = ts_worksheet.cell(ts_label_cell.row, ts_label_cell.col + 1).value
        
        report_data["SpreadSheetURL"] =  "docs.google.com/spreadsheets/d/{}".format(record_dict["CurrentSpreadSheet"].id)
        
        return report_data
    else:
        pass   



# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    if user_check(message) == True:
            bot.send_message(message.chat.id, "Welcome {}\nUser: {}  ".format(message.from_user.first_name,message.from_user.id))
            bot.reply_to(message, "/start & /help to start and get commands\n/add to add record\n/report to get your expense report")
    else:
        pass

#Handle /add
@bot.message_handler(commands=['add'])
def add_record(message):
    if record_dict["User"] is not None:
        sent = bot.send_message(message.chat.id)
        bot.register_next_step_handler(sent,start)
    else:
        pass
    
@bot.message_handler(commands=['report'])
def send_report(message):
    if record_dict["User"] is not None:
        start_markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        start_markup.row('View Report')
        report_data = get_report()
        report_message = "Current month expenses: {}\nTotal expenses: {}\nYou can view your expense report details on Google Sheets: {}".format(report_data["MonthExpenses"], report_data["TotalExpenses"], report_data["SpreadSheetURL"])
        sent = bot.send_message(message.chat.id, report_message, reply_markup=start_markup)
        bot.register_next_step_handler(sent,start)
    else:
        pass
    


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, "out of first loop")



print("I'm listening...")
bot.infinity_polling()