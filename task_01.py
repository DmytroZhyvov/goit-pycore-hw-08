from collections import UserDict
from datetime import datetime, timedelta
import pickle


class Field:
    """Base class for fields"""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Class to store a contact name. Required field"""

    def __init__(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name cannot be empty or contain only spaces")
        super().__init__(value.strip())


class Phone(Field):
    """Class to store phone numbers"""

    def __init__(self, value: str):
        if not isinstance(value, str) or not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """Class to store birthday"""
    def __init__(self, value: str):
        try:
            date = datetime.strptime(value, '%d.%m.%Y').date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(date)

    def date_to_string(self):
        return self.value.strftime('%d.%m.%Y')


class Record:
    """Class to store contact data (name, phone numbers and birthday optionally)"""

    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: list[Phone] = []
        self.birthday: Birthday | None = None

    # Add phone number to a contact
    def add_phone(self, phone_number: str):
        if self.find_phone(phone_number):
            raise ValueError("Phone number already in use. Enter a new phone number.")
        self.phones.append(Phone(phone_number))

    # Delete contact's phone number if it exists
    def remove_phone(self, phone_number: str):
        phone = self.find_phone(phone_number)
        if phone:
            self.phones.remove(phone)
            return True
        return False

    # Edit contact phone number
    def edit_phone(self, current_number: str, new_number: str):
        phone = self.find_phone(current_number)
        if not phone:
            raise ValueError("Phone number not found.")
        if self.find_phone(new_number):
            raise ValueError("Phone number already in use. Enter a new phone number.")

        phone.value = Phone(new_number).value

        return True

    # Find contact phone number
    def find_phone(self, phone_number: str):
        return next((phone for phone in self.phones if phone.value == phone_number), None)

    # Add contact birthday
    def add_birthday(self, date_str: str):
        bday = Birthday(date_str)
        self.birthday = bday
        return True

    def birthday_to_string(self):
        return self.birthday.date_to_string() if self.birthday else None

    def __str__(self):
        phones = '; '.join(phone.value for phone in self.phones) if self.phones else '-'
        bday = self.birthday.date_to_string() if self.birthday else '-'
        return f'Contact name: {self.name.value}, phones: {phones}, birthday: {bday}'


class AddressBook(UserDict):
    """Class to store contact records"""

    # Add a new record
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    # Find a record by contact name
    def find(self, name: str):
        return self.data.get(name)

    # Delete a record by contact name
    def delete(self, name: str):
        if name in self.data:
            del self.data[name]
            return True
        return False

    # Return a list of contacts having birthdays in 7 days (including today date)
    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for contact in self.data.values():
            if not contact.birthday:
                continue
            birthday_this_year = contact.birthday.value.replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            days_delta = (birthday_this_year - today).days

            if 0 <= days_delta <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": contact.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays

DB_FILENAME = 'addressbook.pkl'
# Save data to AddressBook
def save_data(book: AddressBook, filename: str = DB_FILENAME):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

# Load data from AddressBook
def load_data(filename: str = DB_FILENAME):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    """Error handling function"""

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return f"Error: {e}"
        except IndexError:
            return "Error: Missing arguments. Please provide all required values."
        except TypeError:
            return "Error: Invalid command format. Try again."
        except KeyError:
            return "Error: key not found."
        except Exception:
            return "Error: Invalid command or arguments. Try again."
    return inner


def parse_input(user_input):
    """Parse user input"""
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    """Add contact to list of contacts"""

    if len(args) < 2:
        raise ValueError("Enter contact name and phone number with 10 digits")

    name, phone, *_ = args
    validated_record = Phone(phone)
    record = book.find(name)
    created_record = False

    if record is None:
        record = Record(name)
        book.add_record(record)
        created_record = True

    record.add_phone(validated_record.value)
    return "Contact added." if created_record else "Contact updated."


@input_error
def change_contact(args, book: AddressBook):
    """Change contact phone number"""

    if len(args) < 3:
        raise ValueError("Enter contact name, old phone number and new phone number with 10 digits")

    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if not record:
        raise ValueError("Contact does not exist. Try again.")
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args, book: AddressBook):
    """Show contact phone number"""

    if len(args) < 1:
        raise ValueError("Enter contact name")

    name, *_ = args
    record = book.find(name)
    if not record:
        return "Contact does not exist. Try again."
    if not record.phones:
        return f"{name}: —"
    return f"{name}: {', '.join(p.value for p in record.phones)}"


@input_error
def show_all(book: AddressBook):
    """Show all contacts"""

    if not book.data:
        return "No contacts found."
    lines = []
    for record in book.data.values():
        lines.append(str(record))
    return "\n".join(lines)


@input_error
def add_birthday(args, book: AddressBook):
    """ Add contact birthday"""

    if len(args) < 2:
        raise ValueError("Enter contact name and birthday DD.MM.YYYY")

    name, date_str, *_ = args
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_birthday(date_str)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    """Show contact birthday"""

    if len(args) < 1:
        raise ValueError("Enter contact Name")

    name, *_ = args
    record = book.find(name)
    if not record:
        return "Contact does not exist."
    if not record.birthday:
        return f"{name}: birthday not added."
    return f"{name}: {record.birthday_to_string()}"


@input_error
def birthdays(args, book: AddressBook):
    """Show upcoming birthdays within 7 days"""

    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays within the next 7 days."
    grouped = {}
    for item in upcoming:
        date = item["congratulation_date"]
        grouped.setdefault(date, []).append(item["name"])
    lines = []
    for date, names in grouped.items():
        lines.append(f"{date}: {', '.join(names)}")
    return "\n".join(lines)

def save(book: AddressBook, filename: str=DB_FILENAME):
    save_data(book, filename)
    return "Saved successfully."

def main():
    book = load_data(DB_FILENAME)
    print("Welcome to the assistant bot!")
    try:
        while True:
            user_input = input("Enter a command: ")
            if not user_input:
                continue

            try:
                command, *args = parse_input(user_input)
            except Exception:
                print("Invalid command.")
                continue

            if command in ["close", "exit"]:
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(args, book))

            else:
                print("Invalid command.")
    except KeyboardInterrupt:
        print("Error. Exiting...")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()
