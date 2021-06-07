# **Library Management**


## Table of content
- Description
- Build with
- Dependencies
- Instructions
- Screenshot
  - Dashboard
  - Books
  - Members
  - Transactions
  - Import Books
  - Reports
- Issues



### **Description**

A web application to ease librarian work.
This library management system allows a librarian to track books and their quantity, books issued to members, book fees.

This application allows:

- Librarian to perform general create, update, read, delete operations on Books and Members.
- Issue a book to a member.
- Issue a book return from a member.
- Search for a book by name and author.
- Charge a rent fee on book returns.
- Doesn't allows a member to issue books if outstanding debt is more than Rs.500

Also providing librarian's an option to import books using Frappe API & download our pdf report.

### Built With

- [Flask](https://flask.palletsprojects.com/en/2.0.x/http:// "Flask") - Backend
- [SQLAlchemy](http://https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/ "SQLAlchemy") - Database
- [Bootstrap](http://https://getbootstrap.com/docs/4.0/getting-started/introduction/ "Bootstrap") - Web Framework
- [Templating](http://https://flask.palletsprojects.com/en/1.1.x/templating/ "Templating") - Jinja2


### **Dependencies**

- Flask
- cerely
- Pdfkit
- Wkhtmltopdf
- request

### **Instructions**

These instructions will guide you get a copy of this project up and running on your local machine for development and testing purposes.

Clone the repo

git clone https://github.com/ElishaDallu/library.git

Install the dependencies -  Flask

    pip3 install -r requirements.txt

Getting the Flask server running

    cd library
    python3 lib_main.py

The production build is now running through the flask server on http://localhost:5000/


### **Screenshots**

#### Dashboard

![dashboard](https://user-images.githubusercontent.com/54392846/120594870-2cf31f00-c45f-11eb-9f51-7b9bf79ce059.png)

#### Books

![books](https://user-images.githubusercontent.com/54392846/120306719-c1d70a80-c2ef-11eb-9d59-09d083da287e.png)


#### Members

![members](https://user-images.githubusercontent.com/54392846/120306732-c6032800-c2ef-11eb-9962-ed9113721cb9.png)


#### Transactions

![transactions](https://user-images.githubusercontent.com/54392846/120594425-8f97eb00-c45e-11eb-80dd-dbb87f5653b4.png)

#### Import Books

![import_books](https://user-images.githubusercontent.com/54392846/120306729-c4d1fb00-c2ef-11eb-919d-fd33073ac779.png)

#### Reports

![reports](https://user-images.githubusercontent.com/54392846/120594465-9aeb1680-c45e-11eb-8858-e85252133ede.png)


### **Issues**

Applications unit testing -- pending


