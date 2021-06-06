from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from models import db, Book, Member, Transaction
from datetime import datetime
from tasks import make_celery
from ast import literal_eval
from sqlalchemy import text, and_
import pdfkit
import random
import requests
import json

# initialization block
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'secret_key'
app.config.update(CELERY_BROKER_URL='localhost', CELERY_RESULT_BACKEND='localhost')
celery = make_celery(app)
db.init_app(app)

# --------xx FRAPPE API URL xx--------
url = 'https://frappe.io/api/method/frappe-library'


# --------xx Database Creation block xx--------
@app.before_first_request
def create_table():
    db.create_all()


# --------xx Book routes xx--------
@celery.task()
@app.route('/', methods=['GET', 'POST'])
@app.route('/download', methods=['GET', 'POST'])
def reports():
    results = db.engine.execute(text(
        "SELECT  id, title, authors, average_rating, available_quantity, total_quantity FROM Book WHERE is_valid==True ORDER BY average_rating DESC LIMIT 20"))

    highest_rating = db.engine.execute(text(
        "SELECT title, average_rating FROM Book WHERE average_rating <= 5 ORDER BY average_rating desc LIMIT 1"))

    tot_available_qty = db.engine.execute(text(
        "SELECT Sum(total_quantity) total_quantity, Sum(available_quantity) available_quantity FROM Book"))

    highest_paying_members = db.engine.execute(text(
        "SELECT (SELECT member_fname FROM member WHERE id=member_id) as member_fame, SUM(rent) as rent FROM \"transaction\" WHERE status = 'returned' GROUP BY member_id ORDER BY rent DESC LIMIT 3"))

    if request.method == 'GET':
        if reports is None:
            return render_template('reports.html', results=results, highest_rating=highest_rating,
                                   tot_available_qty=tot_available_qty, highest_paying_members=highest_paying_members)
        else:
            flash('Nothing here!', category='error')
            return render_template('reports.html', results=results, highest_rating=highest_rating,
                                   tot_available_qty=tot_available_qty, highest_paying_members=highest_paying_members)
    elif request.method == 'POST':
        rendered = render_template('download_pdf.html', results=results, highest_paying_members=highest_paying_members)

        # Use False instead of output path to save pdf to a variable
        pdf = pdfkit.from_string(rendered, False)

        response = make_response(pdf)
        # modifying file headers
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=report' + str(datetime.utcnow()) + '.pdf'
        return response


@app.route('/books/<int:page_num>', methods=['GET', 'POST'])
def books(page_num):
    if request.method == 'POST':
        if request.form['title']:
            title = request.form['title'].strip()
            search_title = f"%{title}%"
            search_result = Book.query.filter(Book.title.like(search_title)).all()
            if search_result:
                return render_template("search_result.html", search_result=search_result)
            else:
                flash("No such data!", category='error')
                return render_template("search_result.html", search_result=search_result)
        elif request.form['authors']:
            authors = request.form['authors'].strip()
            search_authors = f"%{authors}%"
            search_result = Book.query.filter(Book.authors.like(search_authors)).all()
            if search_result:
                return render_template("search_result.html", search_result=search_result)
            else:
                flash("No such data!", category='error')
                return render_template("search_result.html", search_result=search_result)
        else:
            title = request.form['title'].strip()
            authors = request.form['authors'].strip()
            search_title = f"%{title}%"
            search_authors = f"%{authors}%"
            search_result = Book.query.filter(
                and_(Book.title.like(search_title), Book.authors.like(search_authors))).all()
            if search_result:
                return render_template("search_result.html", search_result=search_result)
            else:
                flash("No such data!", category='error')
                return render_template("search_result.html", search_result=search_result)
    else:
        all_books = Book.query.paginate(per_page=20, page=page_num)
        if all_books.has_next:
            return render_template('all_books.html', all_books=all_books)
        else:
            flash("No books to display, Please import or add data to view here!", category='error')
            return render_template('all_books.html', all_books=all_books)


@celery.task()
@app.route('/import_books', methods=['GET', 'POST'])
def import_books():
    if request.method == 'POST':
        title = ''
        authors = ''
        isbn = ''
        publisher = ''

        inputs = []

        if request.form['title']:
            inputs.append(request.form['title'].strip())
            title = request.form['title']

        if request.form['authors']:
            inputs.append(request.form['authors'].strip())
            authors = request.form['authors']

        if request.form['isbn']:
            inputs.append(request.form['isbn'].strip())
            isbn = request.form['isbn']

        if request.form['publisher']:
            inputs.append(request.form['publisher'].strip())
            publisher = request.form['publisher']

        if len(inputs) == 0:
            flash("Please enter one of the field to import book other than 'Number of books to import'",
                  category="error")
            return render_template('import_books.html')

        if request.form['no_of_books']:
            inputs.append(request.form['no_of_books'].strip())
            no_of_books = request.form['no_of_books']
        else:
            no_of_books = 1
        import_book(title, authors, isbn, publisher, '', no_of_books)
        flash('Books imported', category='success')
        return redirect(url_for('books', page_num=1))
    return render_template('import_books.html')


@celery.task()
@app.route('/import_all_books', methods=['GET', 'POST'])
def import_all_books():
    page = 1
    data = True
    while data:
        returned_books_from_func = import_book('', '', '', '', page, 1)
        if len(returned_books_from_func) > 0:
            page = page + 1
        else:
            data = False
    flash('All Books Imported!!!', category='success')
    return redirect(url_for('books', page_num=1))


def import_book(title=None, authors=None, isbn=None, publisher=None, page=None, no_of_books=None):
    imported_books = []
    params = {"title": title,
              "authors": authors,
              "isbn": isbn,
              "publisher": publisher,
              "page": page}
    data_from_frappe = requests.get(url, params=params)
    data_content = data_from_frappe.content
    data_literal = literal_eval(data_content.decode('utf8'))
    data_dumps = json.dumps(data_literal)
    json_books = json.loads(data_dumps)
    for book in json_books['message']:
        title = book['title']
        authors = book['authors']
        db_book = Book.query.filter_by(is_valid=True).filter_by(title=title).filter_by(authors=authors).first()
        if db_book:
            db_book.total_quantity = db_book.total_quantity + int(no_of_books)
            db_book.available_quantity = db_book.available_quantity + int(no_of_books)
            db.session.commit()
        else:
            api_book = Book(total_quantity=no_of_books,
                            available_quantity=no_of_books,
                            bookID=book['bookID'].strip(),
                            title=book['title'].strip(),
                            authors=book['authors'].strip(),
                            average_rating=validate_float(book['average_rating'].strip()),
                            # validation of average rating
                            isbn=book['isbn'].strip(),
                            isbn13=book['isbn13'].strip(),
                            language_code=book['language_code'].strip(),
                            num_pages=book['  num_pages'].strip(),
                            ratings_count=book['ratings_count'].strip(),
                            text_reviews_count=book['text_reviews_count'].strip(),
                            publication_date=book['publication_date'].strip(),
                            publisher=book['publisher'].strip())

            # validating isbn
            if isValueIsbn(book['isbn'].strip()):
                api_book.is_valid = True
            else:
                api_book.is_valid = False
                api_book.reason = "Invalid Isbn..."

            imported_books.append(api_book)
            db.session.add_all(imported_books)
            # sync the temporary state of application data with the permanent state of the data ( in a database, or on disk)
            db.session.flush()
            db.session.commit()

    return imported_books


def validate_float(value):
    try:
        return float(value)
    except ValueError:
        # Generate random float values
        return random.uniform(0, 5)


def isValueIsbn(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title'].strip()
        authors = request.form['authors'].strip()
        total_quantity = request.form['total_quantity']
        book = Book.query.filter_by(is_valid=True).filter_by(title=title).filter_by(authors=authors).first()
        if book:
            book.quantity = int(book.total_quantity) + int(request.form['total_quantity'])
            db.session.commit()
            return redirect(url_for('books', page_num=1))
        else:
            book = Book(title=title, authors=authors, total_quantity=total_quantity, available_quantity=total_quantity)
            insert_book(book)
            flash('Book Added!', category='success')
            return redirect(url_for('books', page_num=1))


@app.route('/update_book/<id>', methods=['POST'])
def update_book(id):
    book = Book.query.filter_by(id=id).first()
    if request.method == 'POST':
        if book:
            if request.form['title']:
                book.title = request.form['title'].strip()
            if request.form['authors']:
                book.authors = request.form['authors'].strip()
            if request.form['isbn']:
                book.isbn = request.form['isbn']
            if request.form['isbn13']:
                book.isbn13 = request.form['isbn13']
            if request.form['num_pages']:
                book.num_pages = request.form['num_pages']
            if request.form['publisher']:
                book.publisher = request.form['publisher'].strip()
            if request.form['total_quantity']:
                book.total_quantity = request.form['total_quantity']
                book.available_quantity = request.form['total_quantity'] + str(book.available_quantity)

            if int(book.available_quantity) > int(book.total_quantity):
                book.available_quantity = book.total_quantity

            book.date_updated = datetime.utcnow()
            db.session.commit()
            flash('Book Updated!', category='success')
            return redirect(url_for('books', page_num=1))


@app.route('/delete_book/<id>', methods=['GET', 'POST'])
def delete_book(id):
    issued_book = Transaction.query.filter_by(book_id=id).filter_by(status='issued').first()
    book = Book.query.filter_by(id=id).first()
    if request.method == 'GET':
        return render_template('delete_book.html', book=book, title='Delete Book')
    if request.method == 'POST':
        if issued_book:
            flash('Cannot perform operation as book is issued to a member!', category='error')
            return redirect(url_for('books', page_num=1))
        else:
            db.session.delete(book)
            db.session.commit()
            flash('Book data deleted successfully!', category='error')
            return redirect(url_for('books', page_num=1))


@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        member_fname = request.form['member_fname'].strip()
        member_lname = request.form['member_lname'].strip()
        title_id = request.form['title_id']
        authors_id = request.form['authors_id']

        member = Member.query.filter_by(member_fname=member_fname).filter_by(member_lname=member_lname).first()
        if member is None:
            flash('Member does not exist, Please add member to issue book', category='error')
            return render_template('issue_book.html', books=get_books())
        else:
            title_book = Book.query.get(int(title_id))
            authors_book = Book.query.get(int(authors_id))
            book = Book.query.filter_by(id=title_id).first()

            data = fetch_books_by_member_id(member.id)
            debt = sum(d.rent for d in data)

            already_issued = Transaction.query.filter(
                and_(Transaction.book_id == book.id, Transaction.member_id == member.id,
                     Transaction.status == 'issued')).first()

            if not member:
                flash('Invalid member data, Please enter a valid input', category='error')
                return render_template('issue_book.html', books=get_books())
            elif title_book.id != authors_book.id:
                flash('Book does not exist, Please enter a valid input', category='error')
                return render_template('issue_book.html', books=get_books())
            elif debt >= 500:
                flash('Please clear your outstanding debt to issue books', category='error')
                return render_template('issue_book.html', books=get_books())
            elif already_issued:
                flash("Book Already Issued!", category="error")
                return render_template('issue_book.html', books=get_books())
            elif book.available_quantity == 0:
                flash('Book is unavailable right now, Please come back later!')
                return render_template('issue_book.html', books=get_books())
            else:
                data = Transaction(book_id=title_book.id, member_id=member.id, status='issued',
                                   issue_date=datetime.utcnow())
                db.session.add(data)
                title_book.available_quantity = title_book.available_quantity - 1
                db.session.commit()
                flash(f"Book Issued  to {member.member_fname} {member.member_lname}!", category='Success')
                return redirect(url_for('books', page_num=1))

    return render_template('issue_book.html', books=get_books())


@app.route('/return_book', methods=['POST'])
def return_book():
    if request.method == 'POST':
        if 'member_fname' and 'member_lname' in request.form:
            member_fname = request.form['member_fname'].strip()
            member_lname = request.form['member_lname'].strip()
            member = Member.query.filter_by(member_fname=member_fname).filter_by(member_lname=member_lname).first()
            data = []
            if member:
                data = fetch_books_by_member_id(member.id)
            else:
                flash('Member not found, Please check for typing error and try again!', category='error')
            return render_template('return_book_data.html', data=data,
                                   member_fname=member_fname, member_lname=member_lname)


def fetch_books_by_member_id(id):
    data = []
    if id:
        issued_books_data = Transaction.query.filter_by(member_id=id).filter_by(status='issued').all()
        for trans in issued_books_data:
            book_data = Book.query.filter_by(id=trans.book_id).filter_by(is_valid=True).first()
            issue_for_days = datetime.utcnow().day - trans.issue_date.day
            if issue_for_days == 0:
                rnt = 100
            else:
                rnt = issue_for_days * 100
            data.append(ReturnBook(id=trans.id,
                                   title=book_data.title,
                                   authors=book_data.authors,
                                   rent=rnt,
                                   memberId=id))
    return data


class ReturnBook:
    def __init__(self, id, title, authors, rent, memberId):
        self.id = id
        self.title = title
        self.authors = authors
        self.rent = rent
        self.memberId = memberId


@app.route('/confirm_return', methods=['GET', 'POST'])
def confirm_return():
    if request.method == 'POST':
        if not request.form.getlist("chk_bx"):
            flash('Please check the box to return books')
        else:
            tran_ids = request.form.getlist("chk_bx")
            for id in tran_ids:
                trans = Transaction.query.get(int(id))
                trans.status = 'returned'
                trans.return_date = datetime.utcnow()

                issue_for_days = datetime.utcnow().date() - trans.issue_date.date()
                trans.issued_for_days = issue_for_days.days
                if trans.issued_for_days == 0:
                    trans.issued_for_days = 1
                    trans.rent = 100
                else:
                    trans.rent = issue_for_days.days * 100
                book_id = trans.book_id
                book = Book.query.filter_by(id=book_id).filter_by(is_valid=True).first()
                book.available_quantity = book.available_quantity + 1
                db.session.commit()

            flash('Book has been returned, Thank you...')
            return redirect(url_for('books', page_num=1))


def get_books():
    return Book.query.all()


def insert_book(book):
    db.session.add(book)
    db.session.commit()


# --------xx member routes xx--------
@app.route('/members/<int:page_num>', methods=['GET'])
def members(page_num):
    if request.method == 'GET':
        all_members = Member.query.paginate(per_page=20, page=page_num)
        if all_members.has_next:
            return render_template('all_members.html', all_members=all_members)
        else:
            flash('No member! Please add member!', category='error')
            return render_template('all_members.html', all_members=all_members)


@app.route('/member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        member_fname = request.form['member_fname'].strip()
        member_lname = request.form['member_lname'].strip()
        member_address = request.form['member_address'].strip()
        member = Member.query.filter_by(member_fname=member_fname).filter_by(member_lname=member_lname).first()
        if member:
            flash('Member data already exist, Please use something different!', category='error')
            return redirect(url_for('members', page_num=1))
        else:
            member = Member(member_fname=member_fname, member_lname=member_lname, member_address=member_address)
            db.session.add(member)
            db.session.commit()
            flash('Member data added successfully!', category='success')
            return redirect(url_for('members', page_num=1))


@app.route('/update_member/<id>', methods=['POST'])
def update_member(id):
    if request.method == 'POST':
        member = Member.query.filter_by(id=id).first()
        if member:
            if request.form['member_fname']:
                member.member_fname = request.form['member_fname'].strip()
            if request.form['member_lname']:
                member.member_lname = request.form['member_lname'].strip()
            if request.form['member_address']:
                member.member_address = request.form['member_address'].strip()
            member.date_updated = datetime.utcnow()
            db.session.commit()
            flash('Member data updated successfully!', category='success')
            return redirect(url_for('members', page_num=1))


@app.route('/delete_member/<id>', methods=['GET', 'POST'])
def delete_member(id):
    member = Member.query.filter_by(id=id).first()
    member_with_issued_book = Transaction.query.filter_by(member_id=id).filter_by(status='issued').first()
    if request.method == 'GET':
        return render_template('delete_member.html', member=member, title='Delete member')
    if request.method == 'POST':
        if member_with_issued_book:
            flash('Cannot perform operation as member has issued book', category='error')
            return redirect(url_for('members', page_num=1))
        else:
            db.session.delete(member)
            db.session.commit()
            flash('Member data deleted successfully!', category='error')
            return redirect(url_for('members', page_num=1))


@app.route('/transactions/<int:page_num>', methods=['GET', 'POST'])
def transactions(page_num):
    transactions_data = Transaction.query.join(Member, Transaction.member_id == Member.id).add_columns(Transaction.id,
                                                                                                       Transaction.book_id,
                                                                                                       Member.member_fname,
                                                                                                       Member.member_lname,
                                                                                                       Transaction.status,
                                                                                                       Transaction.issue_date,
                                                                                                       Transaction.return_date,
                                                                                                       Transaction.issued_for_days,
                                                                                                       Transaction.rent).paginate(
        per_page=20, page=page_num)
    if transactions_data.has_next:
        return render_template('transactions.html', transactions_data=transactions_data)
    else:
        flash('No transactions taken place yet!', category='error')
        return render_template('transactions.html', transactions_data=transactions_data)



# --------xx about page routes xx--------
@app.route('/about')
def about():
    return render_template('about.html', title='About')


app.run(debug=True)
