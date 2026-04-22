# import pandas as pd
# import numpy as np

# np.random.seed(42)

# # Config
# dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")
# products = [
#     ("P101", "Protein Powder"),
#     ("P102", "Peanut Butter"),
#     ("P103", "Oats"),
#     ("P104", "Almonds"),
#     ("P105", "Milk Powder"),
#     ("P106", "Chana Sattu"),
#     ("P107", "Brown Rice"),
#     ("P108", "Paneer"),
#     ("P109", "Curd"),
#     ("P110", "Energy Bars")
# ]
# regions = ["North", "South", "East", "West"]

# data = []

# for date in dates:
#     for pid, pname in products:
#         region = np.random.choice(regions)

#         # 🎯 Seasonality factor
#         month = date.month
#         if month in [4,5,6]:  # Summer
#             seasonal_factor = 1.3
#         elif month in [7,8,9]:  # Monsoon
#             seasonal_factor = 1.5
#         elif month in [10,11]:  # Festive
#             seasonal_factor = 1.7
#         else:
#             seasonal_factor = 0.9

#         # 📉 Base demand
#         base_demand = np.random.randint(40, 120)

#         # 💰 Price variation
#         base_price = {
#             "P101": 500, "P102": 300, "P103": 150, "P104": 800,
#             "P105": 400, "P106": 120, "P107": 200, "P108": 350,
#             "P109": 90, "P110": 250
#         }[pid]

#         price = base_price + np.random.randint(-50, 50)

#         # 📊 Units sold with noise
#         units = int(base_demand * seasonal_factor + np.random.normal(0, 10))

#         # ⚠️ Inject anomalies (real-world behavior)
#         if np.random.rand() < 0.01:
#             units *= 3  # sudden spike
#         if np.random.rand() < 0.01:
#             units = max(0, units - 100)  # sudden drop

#         # ❌ Invalid data (for validation testing)
#         if np.random.rand() < 0.005:
#             units = -units  # negative case
#         if np.random.rand() < 0.005:
#             price = -price

#         revenue = units * price

#         data.append([date, pid, pname, region, units, price, revenue])

# df = pd.DataFrame(data, columns=[
#     "Date", "Product_ID", "Product_Name",
#     "Region", "Units_Sold", "Price", "Revenue"
# ])

# # ⚠️ Missing values simulation
# for col in ["Region", "Units_Sold"]:
#     df.loc[df.sample(frac=0.01).index, col] = None

# # Save
# df.to_csv("final_sales_dataset.csv", index=False)

# print("Dataset generated:", df.shape)


class student ():
    students =[]
    def __init__(self,name,age):
        self.name = name
        self.age = age
        student.students.append(self)


def add_students():
    number = int(input("Enter the number of students you want to add : "))
    for i in range (number):
        name = input(f"Enter the name of student {i+1} : ")
        age = int(input(f"Enter the age of student {i+1} : "))
        student(name,age)
   
def details():
    details = int(input("Enter the number of students you want to see details of : "))
    if details > len(student.students):
        print(f"Enter a valid number of students.\nNumber of available students: {len(student.students)}.\n Your input : {details}")
    else:
        for i in range(details):
            print(f"Name of student {i+1}: {student.students[i].name} , Age : {student.students[i].age}")
    

add_students()
details()

