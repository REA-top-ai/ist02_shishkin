from abc import ABC, abstractmethod


class User:
    def __init__(self, id, role):
        self.id = id
        self.role = role
    
    def say_user_info(self):
        print(f"User ID: {self.id}, Role: {self.role}")


class AbstractEmployee(ABC):
    new_id = 1
    
    def __init__(self):
        self.id = AbstractEmployee.new_id
        AbstractEmployee.new_id += 1
        self._name = None
        self._id = None
        self.__id = None
    
    @abstractmethod
    def say_id(self):
        pass


class Employee(AbstractEmployee):
    def say_id(self):
        print(f"My id is {self.id}")
    
    def get_name(self):
        return self._name
    
    def set_name(self, name):
        self._name = name
    
    def del_name(self):
        del self._name


class Admin(Employee, User):
    def __init__(self):
        Employee.__init__(self)
        User.__init__(self, self.id, "Admin")
    
    def say_id(self):
        super().say_id()
        print("I am an Admin")


class Manager(Admin):
    def say_id(self):
        super().say_id()
        print("I am in charge!")


class Meeting:
    def __init__(self):
        self.attendees = []
    
    def __len__(self):
        return len(self.attendees)
    
    def __add__(self, employee):
        self.attendees.append(employee)
        return self


e1 = Employee()
e2 = Employee()
e3 = Admin()
e4 = Manager()

e1.say_id()
e2.say_id()
e3.say_id()
e4.say_id()

e3.say_user_info()

meeting = [Employee(), Admin(), Manager()]

for person in meeting:
    person.say_id()

m1 = Meeting()
m1 + e1 + e2 + e3
print(len(m1))

print("\n--- dir(e1) ---")
print(dir(e1))