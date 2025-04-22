# from members.models import User 

# User.objects.all()

# user1 = User(
#     user_id = 1,
#     user_name = "John_Doe",
#     email = "johndoe@gmail.com",
#     phone_num = "0123456789",
#     address = "1234 W Doe Ave",
#     password = "123",
#     payment_option = "Paypal",
#     identification = "Real ID",
#     dark_mode = False,
#     language = "English"
# )

# customer1 = Customer(user_id = user1)

# customer_description_1 = Customer_Description(description = "Very nice!", customer_id=customer1)

# from members.models import Customer_Rating, User

# # Retrieve an existing user (ensure the user exists in the database)
# user = User.objects.get(user_id=1)  # Adjust the user_id accordingly

# # Create a new customer rating
# rating = Customer_Rating.objects.create(
#     rate=Customer_Rating.RatingChoices.FIVE_STAR,  # Using enum for clarity
#     user_id=user
# )

# print("Customer rating created:", rating)






# user2 = User(
#     user_id = 2,
#     user_name = "Jane_Doe",
#     email = "janedoe@gmail.com",
#     phone_num = "1234567890",
#     address = "1234 E Doe Ave",
#     password = "456",
#     payment_option = "Paypal",
#     identification = "Real ID",
#     dark_mode = False,
#     language = "English"
# )

# user3 = User(
#     user_id = 3,
#     user_name = "Lene",
#     email = "lene@gmail.com",
#     phone_num = "1023456789",
#     address = "1234 W Len Ave",
#     password = "012",
#     payment_option = "Paypal",
#     identification = "Real ID",
#     dark_mode = False,
#     language = "English"
# )

# user4 = User(
#     user_id = 4,
#     user_name = "Doe",
#     email = "doe@gmail.com",
#     phone_num = "0123456788",
#     address = "1234 S Doe Ave",
#     password = "789",
#     payment_option = "Paypal",
#     identification = "Real ID",
#     dark_mode = False,
#     language = "English"
# )

# # user_list = [user1, user2, user3, user4]

# # for x in user_list:
# #     x.save()



# # encypting the password when user is registering  

# def hash_password(password: str) -> str:
#     """Hash a password using bcrypt."""
#     salt = bcrypt.gensalt()
#     hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
#     return hashed_password.decode('utf-8')

# def check_password(password: str, hashed_password: str) -> bool:
#     """Check if a password matches its hashed version."""
#     return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

# # Example Usage
# if __name__ == "__main__":
#     password = "my_secure_password"
#     hashed_pw = hash_password(password)
#     print(f"Hashed Password: {hashed_pw}")

#     # Verify password
#     is_valid = check_password("my_secure_password", hashed_pw)
#     print(f"Password Match: {is_valid}")



# from django.shortcuts import render, redirect
# from django.http import HttpResponse, HttpRequest
# from django.template import loader
# # from django.contrib.auth.forms import UserCreationForm
# from django.conf import settings


# # security 
# from django.contrib.auth.hashers import make_password

# def members(request):
#     template = loader.get_template('app.html')
#     return render(request, "app.html")

# def register(request):
#     # if request.method == "POST":
#     #     form = UserCreationForm(request.POST)
#     #     if form.is_valid():
#     #         form.save()
#     #         return redirect("post:list")
#     # else:
#     #     form = UserCreationForm()
#     if request.method == "POST":
#         user_name = request.POST["username"]
#         password = request.POST["pwd"]
#         hashed_pwd = make_password(password)
#         return render(request, "home_page.html", {"user_name": user_name, "password": hashed_pwd})

#     # email = request.POST["email"]
#     # phone_num = request.POST["phone_num"]
#     # address = request.POST["address"]
#     # payment_option = request.POST["payment_option"]
#     # identification = request.POST["id"]


# # def register(request):
# #     template = loader.get_template('home_page.html')
# #     return render(request, "home_page.html")



#     # def members(requests):
# #     template = loader.get_template('app.html')
# #     return HttpResponse(template.render())

#     # template = loader.get_template('app.html')
#     # return HttpResponse(template.render())

# # Create your views here.



# from django.shortcuts import render, redirect
# from django.http import HttpResponse, HttpRequest
# from django.template import loader
# # from django.contrib.auth.forms import UserCreationForm
# from django.conf import settings


# # security 
# from django.contrib.auth.hashers import make_password

# def members(request):
#     template = loader.get_template('members_page.html')
#     return render(request, "members_page.html")

# def app(request):
#     template = loader.get_template('app.html')
#     return render(request, 'app.html')

# def register(request):
#     # if request.method == "POST":
#     #     form = UserCreationForm(request.POST)
#     #     if form.is_valid():
#     #         form.save()
#     #         return redirect("post:list")
#     # else:
#     #     form = UserCreationForm()
#     if request.method == "POST":
#         user_name = request.POST["username"]
#         password = request.POST["pwd"]
#         hashed_pwd = make_password(password)
#         return render(request, "home_page.html", {"user_name": user_name, "password": hashed_pwd})

#     # email = request.POST["email"]
#     # phone_num = request.POST["phone_num"]
#     # address = request.POST["address"]
#     # payment_option = request.POST["payment_option"]
#     # identification = request.POST["id"]

# def login(request):
#     return render(request, "login.html")

# def services_FAQ(request):
#     return render(request, "home_page.html")

# def about_us(request):
#     return render(request, "home_page.html")

# def language(request):
#     return render(request, "home_page.html")


# def dashboard(request):
#     return render(request, "home_page.html")

# def new_job(request):
#     return render(request, "home_page.html")

# def job_list(request):
#     return render(request, "home_page.html")

# def my_account(request):
#     return render(request, "home_page.html")

# def settings(request):
#     return render(request, "home_page.html")


# # def register(request):
# #     template = loader.get_template('home_page.html')
# #     return render(request, "home_page.html")



#     # def members(requests):
# #     template = loader.get_template('app.html')
# #     return HttpResponse(template.render())

#     # template = loader.get_template('app.html')
#     # return HttpResponse(template.render())

# ///////////////////////////////////

# def login(request):
#     if request.method == "POST":
#         # username = request.POST["username"]
#         # password = request.POST["pwd"]
#         username = request.POST.get("username")
#         password = request.POST.get("pwd")
#         # try:
#         user = User_Client.objects.get(user_name=username)
#         if user.check_password(password):
#             # login(request, user)
#             render(request, "home_page.html")
#         else:
#             redirect("members")
#         # user = auth.authenticate(username=username, password=password)
#         # except user is None:
#         #     return redirect("login")

#         # if user is not None:
#         #     return render(request, "dashboard.html")
#         # user = auth.authenticate(username=username, password=password)

#         # if user is not None:
#         #     return render(request, "home_page.html")
#         # else: 
#         #     messages.info(request, 'authentication failed')
#         #     return redirect("members")
#     else: 
#     #     messages.info(request, 'not a post request')
#         return redirect("members")

