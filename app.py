from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os
from functools import wraps
from flask import jsonify
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
import certifi
# MongoDB Configuration
from pymongo.mongo_client import MongoClient
uri = "mongodb+srv://bharshavardhanreddy924:516474Ta@data-dine.5oghq.mongodb.net/?retryWrites=true&w=majority&ssl=true"
client = MongoClient(uri, tlsCAFile=certifi.where())

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
db = client['resta_db']

# File Upload Configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database initialization
def init_db():
    if db.users.count_documents({'username': 'admin'}) == 0:
        db.users.insert_one({
            'username': 'admin',
            'password': generate_password_hash('admin123'),
            'role': 'admin',
            'first_name': 'Admin',
            'last_name': 'User',
            'phone_number': None,
            'hire_date': datetime.now(),
            'work_schedule': None
        })

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Update the root route to show homepage first
@app.route('/')
def homepage():
    return render_template('homepage.html')

# Update the index route to handle authenticated users
@app.route('/dashboard')
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('customer_menu'))
    return redirect(url_for('login'))

# Update login route to redirect to dashboard
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = db.users.find_one({'username': username})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid username or password', 'error')
    return render_template('login.html')

# Update register route to redirect to login after success
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('register'))
        
        if db.users.find_one({'username': username}):
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
        
        user = {
            'username': username,
            'password': generate_password_hash(password),
            'role': 'customer',
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'phone_number': request.form.get('phone_number'),
            'registration_date': datetime.now()
        }
        
        db.users.insert_one(user)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    stats = {
        'dishes_count': db.dishes.count_documents({}),
        'orders_count': db.orders.count_documents({}),
        'ingredients_count': db.ingredients.count_documents({}),
        'low_stock': db.ingredients.count_documents({'QuantityInStock': {'$lte': 10}}),
        'pending_orders': db.orders.count_documents({'OrderStatus': 'Pending'})
    }
    
    recent_orders = list(db.orders.find().sort('OrderTime', -1).limit(5))
    low_stock_items = list(db.ingredients.find({'QuantityInStock': {'$lte': 10}}))
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_orders=recent_orders,
        low_stock_items=low_stock_items
    )

# Employees List Route
@app.route('/admin/employees')
@login_required
@admin_required
def view_employees():
    employees = list(db.employees.find())
    return render_template('admin/employees.html', employees=employees)

# Add Employee Route
@app.route('/admin/employees/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    if request.method == 'POST':
        # Collect form data
        employee_data = {
            "FirstName": request.form.get('FirstName'),
            "LastName": request.form.get('LastName'),
            "PhoneNumber": request.form.get('PhoneNumber'),
            "Designation": request.form.get('Designation'),
            "HireDate": request.form.get('HireDate'),
            "Salary": float(request.form.get('Salary')),
            "WorkSchedule": request.form.get('WorkSchedule'),
            "Age": int(request.form.get('Age')),
            "DOB": request.form.get('DOB')
        }
        # Insert into MongoDB
        db.employees.insert_one(employee_data)
        flash("Employee added successfully!", "success")
        return redirect(url_for('view_employees'))
    
    return render_template('admin/add_employee.html')

# Update Employee Route
@app.route('/admin/employees/update/<id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_employee(id):
    employee = db.employees.find_one({"_id": ObjectId(id)})
    if not employee:
        flash("Employee not found!", "error")
        return redirect(url_for('view_employees'))
    
    if request.method == 'POST':
        # Collect updated data from form
        updated_data = {
            "FirstName": request.form.get('FirstName'),
            "LastName": request.form.get('LastName'),
            "PhoneNumber": request.form.get('PhoneNumber'),
            "Designation": request.form.get('Designation'),
            "HireDate": request.form.get('HireDate'),
            "Salary": float(request.form.get('Salary')),
            "WorkSchedule": request.form.get('WorkSchedule'),
            "Age": int(request.form.get('Age')),
            "DOB": request.form.get('DOB')
        }
        # Update MongoDB document
        db.employees.update_one({"_id": ObjectId(id)}, {"$set": updated_data})
        flash("Employee updated successfully!", "success")
        return redirect(url_for('view_employees'))
    
    return render_template('admin/update_employee.html', employee=employee)

# Delete Employee Route
@app.route('/admin/employees/delete/<id>')
@login_required
@admin_required
def delete_employee(id):
    employee = db.employees.find_one({"_id": ObjectId(id)})
    if not employee:
        flash("Employee not found!", "error")
        return redirect(url_for('view_employees'))
    
    db.employees.delete_one({"_id": ObjectId(id)})
    flash("Employee deleted successfully!", "success")
    return redirect(url_for('view_employees'))

@app.route('/admin/customers')
@login_required
@admin_required
def list_customers():
    try:
        # Create aggregation pipeline to get customer details with order information
        pipeline = [
            {
                '$match': {
                    'role': 'customer'  # Only get users with role 'customer'
                }
            },
            {
                '$lookup': {
                    'from': 'orders',
                    'localField': '_id',
                    'foreignField': 'customer_id',
                    'as': 'orders'
                }
            },
            {
                '$addFields': {
                    'total_orders': {'$size': '$orders'},
                    'total_spent': {'$sum': '$orders.total_price'},
                    'last_order_date': {'$max': '$orders.order_time'},
                    'full_name': {
                        '$concat': [
                            {'$ifNull': ['$first_name', '']}, 
                            ' ',
                            {'$ifNull': ['$last_name', '']}
                        ]
                    }
                }
            },
            {
                '$project': {
                    'full_name': 1,
                    'username': 1,
                    'phone_number': 1,
                    'registration_date': 1,
                    'total_orders': 1,
                    'total_spent': 1,
                    'last_order_date': 1
                }
            },
            {
                '$sort': {'registration_date': -1}  # Sort by newest customers first
            }
        ]

        customers = list(db.users.aggregate(pipeline))
        
        return render_template('admin/customers.html', 
                             customers=customers,
                             title='Customer List')
                             
    except Exception as e:
        flash(f'Error retrieving customer list: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_customer/<customer_id>', methods=['POST'])
@login_required
@admin_required
def delete_customer(customer_id):
    try:
        # Verify the customer exists and has the role "customer"
        customer = db.users.find_one({
            '_id': ObjectId(customer_id),
            'role': 'customer'
        })
        
        if not customer:
            flash('Customer not found or cannot be deleted.', 'error')
            return redirect(url_for('list_customers'))
        
        # Optionally, check if the customer has any active orders.
        # Adjust the order status field and values as needed.
        active_order = db.orders.find_one({
            'customer_id': ObjectId(customer_id),
            '$or': [
                {'status': {'$in': ['Pending', 'Processing']}},
                {'OrderStatus': {'$in': ['Pending', 'Processing']}}
            ]
        })
        if active_order:
            flash('Cannot delete customer: They have active orders.', 'error')
            return redirect(url_for('list_customers'))
        
        # Delete the customer from the database
        result = db.users.delete_one({'_id': ObjectId(customer_id)})
        
        if result.deleted_count:
            flash('Customer deleted successfully.', 'success')
        else:
            flash('Error deleting customer.', 'error')
    
    except Exception as e:
        flash(f'Error deleting customer: {str(e)}', 'error')
    
    return redirect(url_for('list_customers'))


@app.route('/admin/menu')
@login_required
@admin_required
def admin_menu():
    try:
        # Get all dishes and explicitly convert allergen fields
        dishes = list(db.dishes.find())
        
        for dish in dishes:
            # Add image path if image exists
            if dish.get('Image'):
                dish['ImagePath'] = url_for('static', filename=f'images/{dish["Image"]}')
            
            # Ensure proper data types for basic fields
            dish['DishName'] = dish.get('DishName', 'Unnamed Dish')
            dish['Price'] = float(dish.get('Price', 0.00))
            dish['PortionSize'] = dish.get('PortionSize', 'N/A')
            dish['Cuisine'] = dish.get('Cuisine', 'N/A')
            dish['Category'] = dish.get('Category', 'N/A')
            dish['PreparationTime'] = int(dish.get('PreparationTime', 0))
            
            # Explicitly handle allergen fields - convert to boolean and handle various true values
            allergens = ['Wheat', 'Milk', 'Soy', 'Peanut', 'Egg']
            for allergen in allergens:
                # Handle various possible "true" values from MongoDB
                value = dish.get(allergen)
                dish[allergen] = (
                    value is True or  # Boolean True
                    value == 1 or     # Integer 1
                    value == '1' or   # String '1'
                    value == 'true' or # String 'true'
                    value == 'True' or # String 'True'
                    value == 'yes' or  # String 'yes'
                    value == 'Yes'     # String 'Yes'
                )

            # Debug print to verify values (remove in production)
            print(f"Dish: {dish['DishName']}")
            print(f"Allergens: Wheat={dish['Wheat']}, Milk={dish['Milk']}, "
                  f"Soy={dish['Soy']}, Peanut={dish['Peanut']}, Egg={dish['Egg']}")

        return render_template('admin/menu.html', dishes=dishes)
        
    except Exception as e:
        app.logger.error(f"Error in admin menu: {str(e)}")
        return render_template('admin/error.html', 
                             error="Failed to load admin menu. Please try again later.")

@app.route('/admin/edit_ingredient/<ingredient_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ingredient(ingredient_id):
    try:
        ingredient = db.ingredients.find_one({'_id': ObjectId(ingredient_id)})
        if not ingredient:
            flash('Ingredient not found', 'error')
            return redirect(url_for('admin_inventory'))
        
        if request.method == 'POST':
            updates = {
                'IngrName': request.form['name'],
                'QuantityInStock': int(request.form['quantity']),
                'Unit': request.form['unit'],
                'ReorderLevel': int(request.form['reorder_level']),
                'ExpiryDate': datetime.strptime(request.form['expiry_date'], '%Y-%m-%d'),
                'Supplier': request.form.get('supplier', ''),
                'UnitCost': float(request.form.get('unit_cost', 0)),
                'LastModified': datetime.now(),
                'ModifiedBy': session['username']
            }
            
            db.ingredients.update_one(
                {'_id': ObjectId(ingredient_id)},
                {'$set': updates}
            )
            
            flash('Ingredient updated successfully', 'success')
            return redirect(url_for('admin_inventory'))
            
    except Exception as e:
        flash(f'Error updating ingredient: {str(e)}', 'error')
        return redirect(url_for('admin_inventory'))
    
    return render_template('admin/edit_ingredient.html', ingredient=ingredient)

@app.route('/admin/delete_ingredient/<ingredient_id>', methods=['POST'])
@login_required
@admin_required
def delete_ingredient(ingredient_id):
    try:
        # Check if the ingredient is referenced in any dishes
        dish_using_ingredient = db.dishes.find_one({
            'ingredients': ObjectId(ingredient_id)
        })
        
        if dish_using_ingredient:
            flash('Cannot delete ingredient: It is currently used in one or more dishes.', 'error')
            return redirect(url_for('admin_inventory'))
        
        # Delete the ingredient from the database
        result = db.ingredients.delete_one({'_id': ObjectId(ingredient_id)})
        
        if result.deleted_count:
            flash('Ingredient deleted successfully.', 'success')
        else:
            flash('Ingredient not found or error deleting ingredient.', 'error')
    
    except Exception as e:
        flash(f'Error deleting ingredient: {str(e)}', 'error')
    
    return redirect(url_for('admin_inventory'))


# Updated inventory route to include more details
@app.route('/admin/inventory')
@login_required
@admin_required
def admin_inventory():
    ingredients = list(db.ingredients.find())
    return render_template('admin/inventory.html', ingredients=ingredients)


@app.route('/admin/update_dish/<dish_id>', methods=['POST'])
@login_required
@admin_required
def update_dish(dish_id):
    # Logic to handle the dish update
    print(f"Updating dish with ID: {dish_id}")
    return redirect(url_for('menu'))  # Assuming there's a menu route

@app.route('/admin/update_inventory/<ingredient_id>', methods=['POST'])
@login_required
@admin_required
def update_inventory(ingredient_id):
    try:
        new_quantity = int(request.form.get('quantity'))
        new_reorder_level = int(request.form.get('reorder_level'))
        
        updates = {
            'QuantityInStock': new_quantity,
            'ReorderLevel': new_reorder_level,
            'LastRestockedDate': datetime.now(),
            'LastModified': datetime.now(),
            'ModifiedBy': session['username']
        }
        
        db.ingredients.update_one(
            {'_id': ObjectId(ingredient_id)},
            {'$set': updates}
        )
        
        flash('Inventory updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating inventory: {str(e)}', 'error')
    
    return redirect(url_for('admin_inventory'))

@app.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    # Get customer data with order statistics
    pipeline = [
        {
            '$match': {'role': 'customer'}
        },
        {
            '$lookup': {
                'from': 'orders',
                'localField': '_id',
                'foreignField': 'customer_id',
                'as': 'orders'
            }
        },
        {
            '$addFields': {
                'total_orders': {'$size': '$orders'},
                'total_spent': {
                    '$sum': '$orders.total_price'
                },
                'last_order_date': {
                    '$max': '$orders.order_time'
                }
            }
        },
        {
            '$sort': {'total_spent': -1}
        }
    ]
    
    customers = list(db.users.aggregate(pipeline))
    return render_template('admin/customers.html', customers=customers)

@app.route('/admin/customer/<customer_id>')
@login_required
@admin_required
def customer_detail(customer_id):
    # Get detailed customer information with order history
    pipeline = [
        {
            '$match': {'_id': ObjectId(customer_id)}
        },
        {
            '$lookup': {
                'from': 'orders',
                'localField': '_id',
                'foreignField': 'customer_id',
                'as': 'orders'
            }
        },
        {
            '$lookup': {
                'from': 'dishes',
                'localField': 'orders.dishes.dish_id',
                'foreignField': '_id',
                'as': 'ordered_dishes'
            }
        }
    ]
    
    customer = db.users.aggregate(pipeline).next()
    
    # Calculate additional statistics
    stats = {
        'total_orders': len(customer['orders']),
        'total_spent': sum(order['total_price'] for order in customer['orders']),
        'average_order_value': sum(order['total_price'] for order in customer['orders']) / len(customer['orders']) if customer['orders'] else 0,
        'favorite_dishes': get_favorite_dishes(customer['orders']),
        'order_frequency': calculate_order_frequency(customer['orders'])
    }
    
    return render_template('admin/customer_detail.html', customer=customer, stats=stats)

# Helper functions for customer analytics
def get_favorite_dishes(orders):
    dish_count = {}
    for order in orders:
        for dish in order['dishes']:
            dish_id = str(dish['dish_id'])
            if dish_id in dish_count:
                dish_count[dish_id]['count'] += dish['quantity']
            else:
                dish_count[dish_id] = {
                    'count': dish['quantity'],
                    'name': dish['dish_name']
                }
    
    return sorted(
        dish_count.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:5]

def calculate_order_frequency(orders):
    if not orders:
        return "No orders yet"
    
    first_order = min(order['order_time'] for order in orders)
    last_order = max(order['order_time'] for order in orders)
    days_diff = (last_order - first_order).days
    
    if days_diff == 0:
        return "First day customer"
    
    orders_per_month = (len(orders) / days_diff) * 30
    return f"{orders_per_month:.1f} orders per month"

# Bulk update menu items
@app.route('/admin/bulk_menu_update', methods=['POST'])
@login_required
@admin_required
def bulk_menu_update():
    try:
        updates = request.json['updates']
        for item in updates:
            db.dishes.update_one(
                {'_id': ObjectId(item['dish_id'])},
                {'$set': {
                    'Price': float(item['price']),
                    'IsAvailable': item['available'],
                    'LastModified': datetime.now(),
                    'ModifiedBy': session['username']
                }}
            )
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/admin/add_dish', methods=['GET', 'POST'])
@login_required
@admin_required
def add_dish():
    if request.method == 'POST':
        try:
            dish_data = {
                'DishName': request.form['dish_name'],
                'Price': float(request.form['price']),
                'PortionSize': request.form['portion_size'],
                'Cuisine': request.form['cuisine'],
                'Category': request.form['category'],
                'PreparationTime': int(request.form['prep_time']),
                'Description': request.form.get('description', ''),
                'Allergens': {
                    'Wheat': 'wheat' in request.form,
                    'Milk': 'milk' in request.form,
                    'Soy': 'soy' in request.form,
                    'Peanut': 'peanut' in request.form,
                    'Egg': 'egg' in request.form
                },
                'IsAvailable': True,
                'CreatedAt': datetime.now(),
                'LastModified': datetime.now()
            }

            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    dish_data['Image'] = filename

            db.dishes.insert_one(dish_data)
            flash('Dish added successfully', 'success')
            return redirect(url_for('admin_menu'))
            
        except Exception as e:
            flash(f'Error adding dish: {str(e)}', 'error')
            
    return render_template('admin/add_dish.html')

@app.route('/admin/edit_dish/<dish_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_dish(dish_id):
    dish = db.dishes.find_one({'_id': ObjectId(dish_id)})
    if not dish:
        flash('Dish not found', 'error')
        return redirect(url_for('admin_menu'))
    
    if request.method == 'POST':
        try:
            updates = {
                'DishName': request.form['dish_name'],
                'Price': float(request.form['price']),
                'PortionSize': request.form['portion_size'],
                'Cuisine': request.form['cuisine'],
                'Category': request.form['category'],
                'PreparationTime': int(request.form['prep_time']),
                'Description': request.form.get('description', ''),
                'IsAvailable': 'is_available' in request.form,
                'Allergens': {
                    'Wheat': 'wheat' in request.form,
                    'Milk': 'milk' in request.form,
                    'Soy': 'soy' in request.form,
                    'Peanut': 'peanut' in request.form,
                    'Egg': 'egg' in request.form
                },
                'LastModified': datetime.now(),
                'ModifiedBy': session['username']
            }

            # Handle image update if new image is uploaded
            if 'image' in request.files:
                file = request.files['image']
                if file and allowed_file(file.filename):
                    # Delete old image if it exists
                    if dish.get('Image'):
                        old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], dish['Image'])
                        if os.path.exists(old_image_path):
                            os.remove(old_image_path)
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updates['Image'] = filename

            # Update dish in database
            db.dishes.update_one(
                {'_id': ObjectId(dish_id)},
                {'$set': updates}
            )
            
            flash('Dish updated successfully', 'success')
            return redirect(url_for('admin_menu'))
            
        except Exception as e:
            flash(f'Error updating dish: {str(e)}', 'error')
    
    return render_template('admin/edit_dish.html', dish=dish)

@app.route('/admin/delete_dish/<dish_id>', methods=['POST'])
@login_required
@admin_required
def delete_dish(dish_id):
    try:
        # Find the dish first
        dish = db.dishes.find_one({'_id': ObjectId(dish_id)})
        if not dish:
            flash('Dish not found', 'error')
            return redirect(url_for('admin_menu'))
        
        # Delete associated image if it exists
        if dish.get('Image'):
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], dish['Image'])
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Check if dish is used in any active orders
        active_orders = db.orders.find_one({
            'dishes.dish_id': ObjectId(dish_id),
            'status': {'$in': ['Pending', 'Processing']}
        })
        
        # Delete the dish from database
        result = db.dishes.delete_one({'_id': ObjectId(dish_id)})
        
        if result.deleted_count:
            flash('Dish deleted successfully', 'success')
        else:
            flash('Error deleting dish', 'error')
            
    except Exception as e:
        flash(f'Error deleting dish: {str(e)}', 'error')
    
    return redirect(url_for('admin_menu'))

import uuid  # For generating unique IDs




@app.route('/admin/add_ingredient', methods=['GET', 'POST'])
@login_required
@admin_required
def add_ingredient():
    if request.method == 'POST':
        try:
            # Generate a unique IngredientID
            ingredient_id = str(uuid.uuid4())  # Unique identifier
            
            # Collect form data
            ingredient_data = {
                'IngredientID': ingredient_id,  # Unique ID
                'IngrName': request.form['name'].strip(),
                'QuantityInStock': int(request.form['quantity']),
                'Unit': request.form['unit'].strip(),
                'ReorderLevel': int(request.form['reorder_level']),
                'ExpiryDate': datetime.strptime(request.form['expiry_date'], '%Y-%m-%d'),
                'LastRestockedDate': datetime.now(),
                'Supplier': request.form.get('supplier', '').strip(),
                'UnitCost': float(request.form.get('unit_cost', 0)),
            }

            # Validate positive numbers for quantity, reorder level, and unit cost
            if ingredient_data['QuantityInStock'] < 0 or ingredient_data['ReorderLevel'] < 0 or ingredient_data['UnitCost'] < 0:
                flash('Quantity, reorder level, and unit cost must be positive values.', 'error')
                return redirect(url_for('add_ingredient'))

            # Insert into the database
            db.ingredients.insert_one(ingredient_data)
            flash('Ingredient added successfully!', 'success')
            return redirect(url_for('admin_inventory'))
        
        except ValueError:
            flash('Please provide valid input for numeric fields.', 'error')
        except Exception as e:
            flash(f'Error adding ingredient: {str(e)}', 'error')

    return render_template('admin/add_ingredient.html')


@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    pipeline = [
        {
            '$lookup': {
                'from': 'users',
                'localField': 'customer_id',  # Changed from CustomerID
                'foreignField': '_id',
                'as': 'customer'
            }
        },
        {'$unwind': {'path': '$customer', 'preserveNullAndEmptyArrays': True}},
        {
            '$lookup': {
                'from': 'dishes',
                'localField': 'dishes.dish_id',  # Changed from Dishes.DishID
                'foreignField': '_id',
                'as': 'dish_details'
            }
        },
        {'$sort': {'order_time': -1}}  # Changed from OrderTime
    ]
    
    orders = list(db.orders.aggregate(pipeline))
    return render_template('admin/orders.html', orders=orders)

@app.route('/admin/update_order_status/<order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Processing', 'Ready', 'Completed', 'Cancelled']:
        db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'OrderStatus': new_status,
                    'LastUpdated': datetime.now()
                }
            }
        )
        flash('Order status updated successfully', 'success')
    else:
        flash('Invalid order status', 'error')
    
    return redirect(url_for('admin_orders'))

from io import BytesIO
from xhtml2pdf import pisa
from flask import make_response

def render_pdf(template_src, context_dict):
    """
    Render HTML template with context and convert it to a PDF file.
    Returns a BytesIO object containing the PDF.
    """
    html = render_template(template_src, **context_dict)
    result = BytesIO()
    # Convert HTML to PDF using pisa
    pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
    if pdf.err:
        return None
    return result


@app.route('/customer/order/<order_id>/invoice')
@login_required
def download_invoice(order_id):
    # Retrieve order details using the provided order_id
    order = db.orders.find_one({
        '_id': ObjectId(order_id),
        'customer_id': ObjectId(session['user_id'])  # Ensure the order belongs to the logged-in user
    })
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('customer_orders'))

    # For simplicity, assume a fixed tax rate (e.g., 10%)
    tax_rate = 0.10
    tax_amount = order['total_price'] * tax_rate
    grand_total = order['total_price'] + tax_amount

    # Prepare context for the invoice template
    context = {
        'order': order,
        'tax_rate': f"{tax_rate*100:.0f}%",
        'tax_amount': f"{tax_amount:.2f}",
        'grand_total': f"{grand_total:.2f}",
        'date': datetime.now().strftime('%B %d, %Y')
    }
    
    pdf_data = render_pdf('customer/invoice.html', context)
    if pdf_data is None:
        flash('Error generating invoice PDF', 'error')
        return redirect(url_for('order_detail', order_id=order_id))
    
    # Create a response with the PDF data and proper headers for download
    response = make_response(pdf_data.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order_id}.pdf'
    return response
from datetime import datetime, timedelta


import json
from datetime import datetime, timedelta
from bson import ObjectId
from flask import Flask, request, send_file, render_template, flash, redirect, url_for
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import pymongo

from flask import request, redirect, url_for, flash, send_file
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from datetime import datetime, timedelta
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

@app.route('/sales_report_pdf', methods=['GET', 'POST'])
def sales_report_pdf():
    if request.method == 'POST':
        try:
            # Retrieve form data
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            if not start_date or not end_date:
                flash("Please provide both start and end dates.", "error")
                return redirect(url_for('sales_report'))

            # Convert date strings to datetime objects
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            # Extend end date to include the full day
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)

            # Fetch orders within the date range and ignore cancelled orders
            orders = list(db.orders.find({
                'order_time': {'$gte': start_dt, '$lt': end_dt},
                'status': {'$nin': ['Cancelled']}
            }))

            # Calculate key metrics
            total_revenue = sum(order.get('total_price', 0) for order in orders)
            number_of_orders = len(orders)
            avg_order_value = total_revenue / number_of_orders if number_of_orders > 0 else 0

            # Process orders to extract daily sales and top-selling items data
            top_items = {}
            daily_sales = {}
            for order in orders:
                # Accumulate daily sales data
                order_date = order['order_time'].date()
                daily_sales[order_date] = daily_sales.get(order_date, 0) + order.get('total_price', 0)

                # Accumulate dish quantities for top-selling items
                for item in order.get('dishes', []):
                    dish_name = item.get('dish_name', 'Unknown')
                    quantity = item.get('quantity', 0)
                    top_items[dish_name] = top_items.get(dish_name, 0) + quantity

            # Get the top 5 selling items
            top_selling = sorted(top_items.items(), key=lambda x: x[1], reverse=True)[:5]

            # Create a PDF document in memory
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter,
                                    rightMargin=72, leftMargin=72,
                                    topMargin=72, bottomMargin=72)
            styles = getSampleStyleSheet()
            story = []

            # Custom title style
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a237e'),
                spaceAfter=30,
                alignment=1
            )

            # Add the report title and period information
            story.append(Paragraph("DATA-DINE", title_style))
            story.append(Paragraph(f"Sales Report: {start_date} to {end_date}", styles['Heading2']))
            story.append(Spacer(1, 20))

            # Narrative summary
            summary_text = (
                "This report provides an overview of the sales performance over the selected period. "
                "It includes key metrics such as total revenue, the number of orders, and the average order value. "
                "Additionally, the report visualizes the daily sales trends and highlights the top-selling items. "
                "These insights can help guide business decisions and identify growth opportunities."
            )
            story.append(Paragraph(summary_text, styles['BodyText']))
            story.append(Spacer(1, 20))

            # Key Metrics Table
            metrics_data = [
                ['Metric', 'Value'],
                ['Total Revenue', f'Rs {total_revenue:,.2f}'],
                ['Number of Orders', str(number_of_orders)],
                ['Average Order Value', f'Rs {avg_order_value:,.2f}']
            ]
            metrics_table = Table(metrics_data, colWidths=[200, 200])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))

            # -----------------------------
            # Create the Daily Sales Trend Graph
            # -----------------------------
            # Adjust the drawing dimensions to fit in half the page width
            drawing_width = (doc.width / 2) - 20  # leave a little margin inside the cell
            drawing_height = 200

            # Ensure we have at least one data point
            dates = sorted(daily_sales.keys())
            values = [daily_sales[date] for date in dates] if dates else [0]

            daily_sales_drawing = Drawing(drawing_width, drawing_height)
            lc = HorizontalLineChart()
            lc.x = 10
            lc.y = 10
            lc.width = drawing_width - 20
            lc.height = drawing_height - 20
            lc.data = [values]
            lc.lines[0].strokeColor = colors.HexColor('#1a237e')
            lc.lines[0].strokeWidth = 2
            lc.fillColor = colors.HexColor('#e8eaf6')

            # Set up the value axis with a slight margin
            if values and min(values) != max(values):
                lc.valueAxis.valueMin = min(values) * 0.9
                lc.valueAxis.valueMax = max(values) * 1.1
            else:
                lc.valueAxis.valueMin = 0
                lc.valueAxis.valueMax = 10
            lc.valueAxis.gridStrokeColor = colors.grey
            lc.valueAxis.labelTextFormat = 'Rs %d'
            
            # Format date labels for the category axis
            lc.categoryAxis.categoryNames = [d.strftime('%Y-%m-%d') for d in dates] if dates else ['No Data']
            lc.categoryAxis.labels.boxAnchor = 'ne'
            lc.categoryAxis.labels.angle = 30
            daily_sales_drawing.add(lc)

            # -----------------------------
            # Create the Top-Selling Items Bar Chart
            # -----------------------------
            top_items_drawing = Drawing(drawing_width, drawing_height)
            bc = VerticalBarChart()
            bc.x = 10
            bc.y = 10
            bc.width = drawing_width - 20
            bc.height = drawing_height - 20
            if top_selling:
                bc.data = [[qty for _, qty in top_selling]]
                bc.categoryAxis.categoryNames = [name for name, _ in top_selling]
            else:
                bc.data = [[0]]
                bc.categoryAxis.categoryNames = ['No Data']
            bc.bars[0].fillColor = colors.HexColor('#1a237e')
            bc.valueAxis.gridStrokeColor = colors.grey
            bc.categoryAxis.labels.boxAnchor = 'ne'
            bc.categoryAxis.labels.angle = 30
            top_items_drawing.add(bc)

            # -----------------------------
            # Arrange the two graphs side by side in a table
            # -----------------------------
            # Create a table with two cells, one for each graph
            graphs_table = Table(
                [[daily_sales_drawing, top_items_drawing]],
                colWidths=[doc.width / 2, doc.width / 2]
            )
            graphs_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))

            # Add headings for the graphs
            story.append(Paragraph("Sales Visualizations", styles['Heading3']))
            story.append(Spacer(1, 10))
            story.append(graphs_table)
            story.append(Spacer(1, 20))

            # -----------------------------
            # List Top-Selling Items as a Bullet List
            # -----------------------------
            bullet_items = []
            for name, qty in top_selling:
                bullet_items.append(ListItem(Paragraph(f"{name}: {qty} sold", styles['BodyText'])))
            if bullet_items:
                story.append(Paragraph("Top Selling Items:", styles['Heading3']))
                story.append(ListFlowable(bullet_items, bulletType='bullet', start='circle'))
            else:
                story.append(Paragraph("No top-selling items data available.", styles['BodyText']))
            story.append(Spacer(1, 20))

            # Build the PDF and return the file
            doc.build(story)
            buffer.seek(0)
            return send_file(
                buffer,
                as_attachment=True,
                download_name="sales_report.pdf",
                mimetype='application/pdf'
            )

        except Exception as e:
            flash(f"Error generating PDF: {str(e)}", "error")
            return redirect(url_for('sales_report'))

    return "Invalid request method", 405


@app.route('/admin/sales_report', methods=['GET', 'POST'])
@login_required
@admin_required
def sales_report():
    # Default: last 30 days
    today = datetime.now()
    default_start = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    default_end = today.strftime('%Y-%m-%d')

    if request.method == 'POST':
        start_date = request.form.get('start_date', default_start)
        end_date = request.form.get('end_date', default_end)
    else:
        start_date = request.args.get('start_date', default_start)
        end_date = request.args.get('end_date', default_end)
    
    try:
        # Parse dates from string
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)  # include the end date
        
        # Find orders within the date range that are not cancelled (if applicable)
        orders = list(db.orders.find({
            'order_time': {'$gte': start_dt, '$lt': end_dt},
            'status': {'$nin': ['Cancelled']}  # Exclude cancelled orders if desired
        }))
        
        total_revenue = sum(order.get('total_price', 0) for order in orders)
        number_of_orders = len(orders)
        average_order_value = total_revenue / number_of_orders if number_of_orders > 0 else 0

        # Aggregate top-selling items (by summing up quantities across orders)
        top_items = {}
        for order in orders:
            for item in order.get('dishes', []):
                dish_id = str(item.get('dish_id'))
                dish_name = item.get('dish_name') or item.get('DishName', 'N/A')
                quantity = item.get('quantity', 0)
                if dish_id in top_items:
                    top_items[dish_id]['quantity'] += quantity
                else:
                    top_items[dish_id] = {'dish_name': dish_name, 'quantity': quantity}
                    
        # Sort items descending by quantity and take the top 5
        top_selling = sorted(top_items.values(), key=lambda x: x['quantity'], reverse=True)[:5]
        
        # Cuisine-wise sales aggregation
        cuisine_sales = {}
        for order in orders:
            for item in order.get('dishes', []):
                dish_id = item.get('dish_id')
                quantity = item.get('quantity', 0)
                # Lookup dish details in the dishes collection if dish_id is available
                dish = db.dishes.find_one({'_id': ObjectId(dish_id)}) if dish_id else None
                cuisine = dish.get('Cuisine', 'Unknown') if dish else 'Unknown'
                cuisine_sales[cuisine] = cuisine_sales.get(cuisine, 0) + quantity

        # Prepare lists for Chart.js (labels and values)
        cuisine_labels = list(cuisine_sales.keys())
        cuisine_values = [cuisine_sales[label] for label in cuisine_labels]
        
        context = {
            'start_date': start_date,
            'end_date': end_date,
            'total_revenue': f"{total_revenue:.2f}",
            'number_of_orders': number_of_orders,
            'average_order_value': f"{average_order_value:.2f}",
            'top_selling': top_selling,
            'cuisine_labels': json.dumps(cuisine_labels),
            'cuisine_values': json.dumps(cuisine_values)
        }
        return render_template('admin/sales_report.html', **context)
    except Exception as e:
        flash(f'Error generating sales report: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))


import socketio  # For "SocketIO"
from flask_socketio import SocketIO
import spacy  # For "spacy"
import threading  # For "threading"
import pyttsx3  # For "pyttsx3"
import speech_recognition as sr  # For "sr"
from flask_socketio import emit
import json  # For "json"
import requests  # For "requests"
socketio = SocketIO(app, cors_allowed_origins="*")
socketio.emit('message', 'Hello')


# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Constants for Groq
GROQ_API_KEY = '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'  # Replace with your API key
GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'

# Global variables for TTS
tts_lock = threading.Lock()
engine = None

def get_tts_engine():
    """Get or create TTS engine"""
    global engine
    if engine is None:
        engine = pyttsx3.init()
    return engine

def text_to_speech(text):
    """Convert text to speech with error handling"""
    global engine
    try:
        with tts_lock:
            current_engine = get_tts_engine()
            current_engine.stop()
            current_engine.say(text)
            try:
                current_engine.runAndWait()
            except RuntimeError:
                engine = pyttsx3.init()
                engine.say(text)
                engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {str(e)}")

def process_voice_input():
    """Record and process voice input"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service."
        except Exception as e:
            print(f"Voice Input Error: {str(e)}")
            return "Sorry, there was an error processing your voice input."

def load_menu_data():
    """Load menu data from file"""
    try:
        with open("new.txt", "r") as file:
            menu_items = []
            for line in file:
                try:
                    item = json.loads(line.strip())
                    menu_items.append(item)
                except json.JSONDecodeError:
                    continue
            return menu_items
    except FileNotFoundError:
        print("Menu file not found. Using empty menu.")
        return []

menu_data = load_menu_data()

SYSTEM_PROMPT = """You are a helpful assistant for an Indian restaurant. Help with recommendations based on:
- Dietary preferences (veg/non-veg)
- Spice levels
- Regional specialties
- Allergies and restrictions
Provide clear, concise responses with dish descriptions."""

def parse_preferences(message):
    """Parse user preferences from message"""
    return {
        "diet": "veg" if "veg" in message.lower() else "non-veg" if "non-veg" in message.lower() else None,
        "spice_level": "high" if "spicy" in message.lower() else "low" if "mild" in message.lower() else None,
        "max_calories": None,
        "allergens": []
    }

def get_recommendations(preferences):
    """Get menu recommendations based on preferences"""
    filtered_items = menu_data
    if preferences["diet"]:
        filtered_items = [item for item in filtered_items 
                        if item.get("diet", "").lower() == preferences["diet"]]
    if preferences["spice_level"]:
        filtered_items = [item for item in filtered_items 
                        if item.get("spice_level", "").lower() == preferences["spice_level"]]
    return filtered_items[:3]

def get_ai_response(message, recommendations):
    """Get AI response from Groq"""
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': GROQ_MODEL,
                'messages': [
                    {'role': 'system', 'content': SYSTEM_PROMPT},
                    {'role': 'user', 'content': message},
                    {'role': 'assistant', 'content': f"Based on the menu, here are recommendations: {recommendations}"}
                ],
                'temperature': 0.7,
                'max_tokens': 500
            }
        )
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return "Sorry, I couldn't process your request at the moment."
    except Exception as e:
        print(f"AI Response Error: {str(e)}")
        return "Sorry, there was an error getting recommendations."

# Add these new routes
@app.route('/customer/chatbot')
@login_required
def chatbot():
    return render_template('customer/chatbot.html')

@socketio.on('start_voice_input')
def handle_voice_input():
    """Handle voice input websocket event"""
    try:
        text = process_voice_input()
        if text and text != "Sorry, I couldn't understand that.":
            preferences = parse_preferences(text)
            recommendations = get_recommendations(preferences)
            response = get_ai_response(text, recommendations)
            
            tts_thread = threading.Thread(target=text_to_speech, args=(response,))
            tts_thread.daemon = True
            tts_thread.start()
            
            emit('bot_response', {'text': response})
        else:
            emit('bot_response', {'text': text})
    except Exception as e:
        print(f"Voice Handler Error: {str(e)}")
        emit('bot_response', {'text': "Sorry, there was an error processing your request."})

@app.route('/chat', methods=['POST'])
def chat():
    """Handle text chat requests"""
    try:
        message = request.json.get('message', '')
        preferences = parse_preferences(message)
        recommendations = get_recommendations(preferences)
        response = get_ai_response(message, recommendations)
        return jsonify({'response': response})
    except Exception as e:
        print(f"Chat Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    

@app.route('/customer/menu')
@login_required
def customer_menu():
    # Get filter parameters from request
    selected_cuisines = request.args.getlist('cuisine')
    selected_allergens = request.args.getlist('allergen')
    
    # Base query for available dishes
    query = {'IsAvailable': True}
    
    # Add cuisine filter if selected
    if selected_cuisines:
        query['Cuisine'] = {'$in': selected_cuisines}
    
    # Handle allergen filtering
    if selected_allergens:
        # Create a query that excludes dishes with any of the selected allergens
        allergen_conditions = {}
        for allergen in selected_allergens:
            allergen_key = f'Allergens.{allergen}'
            allergen_conditions[allergen_key] = {'$ne': True}
        if allergen_conditions:
            query.update(allergen_conditions)
    
    try:
        # Get dishes based on filters
        dishes = list(db.dishes.find(query))
        
        # Process images and allergens
        for dish in dishes:
            if dish.get('Image'):
                dish['ImagePath'] = url_for('static', filename=f'images/{dish["Image"]}')
            # Ensure Allergens dict exists
            dish['Allergens'] = dish.get('Allergens', {})
        
        # Get all unique categories and cuisines for filters
        all_dishes = list(db.dishes.find({'IsAvailable': True}))
        categories = sorted(set(dish['Category'] for dish in all_dishes))
        cuisines = sorted(set(dish['Cuisine'] for dish in all_dishes if 'Cuisine' in dish))
        
        # Define available allergens for filtering
        available_allergens = ['Wheat', 'Milk', 'Soy', 'Peanut', 'Egg']
        
        return render_template(
            'customer/menu.html',
            dishes=dishes,
            categories=categories,
            cuisines=cuisines,
            available_allergens=available_allergens,
            selected_cuisines=selected_cuisines,
            selected_allergens=selected_allergens,
            show_chatbot=True
        )
        
    except Exception as e:
        flash(f'Error loading menu: {str(e)}', 'error')
        return redirect(url_for('homepage'))


@app.route('/customer/cart', methods=['GET', 'POST'])
@login_required
def customer_cart():
    if 'cart' not in session:
        session['cart'] = []
    
    cart_items = []
    total = 0
    
    for item in session['cart']:
        dish = db.dishes.find_one({'_id': ObjectId(item['dish_id'])})
        if dish:
            item_total = dish['Price'] * item['quantity']
            cart_items.append({
                'dish': dish,
                'quantity': item['quantity'],
                'total': item_total
            })
            total += item_total
    
    return render_template('customer/cart.html', cart_items=cart_items, total=total)

@app.route('/customer/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    dish_id = request.form.get('dish_id')
    quantity = int(request.form.get('quantity', 1))
    
    dish = db.dishes.find_one({'_id': ObjectId(dish_id)})
    if not dish:
        flash('Dish not found', 'error')
        return redirect(url_for('customer_menu'))
    
    if not dish.get('IsAvailable', True):
        flash('This dish is currently unavailable', 'error')
        return redirect(url_for('customer_menu'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if dish is already in cart
    cart = session['cart']
    for item in cart:
        if item['dish_id'] == str(dish_id):
            item['quantity'] += quantity
            session.modified = True
            flash('Cart updated successfully', 'success')
            return redirect(url_for('customer_cart'))
    
    # Add new item to cart
    cart.append({
        'dish_id': str(dish_id),
        'quantity': quantity
    })
    session.modified = True
    flash('Item added to cart', 'success')
    return redirect(url_for('customer_cart'))

@app.route('/customer/update_cart', methods=['POST'])
@login_required
def update_cart():
    dish_id = request.form.get('dish_id')
    quantity = int(request.form.get('quantity', 0))
    
    if 'cart' not in session:
        flash('Cart is empty', 'error')
        return redirect(url_for('customer_cart'))
    
    cart = session['cart']
    if quantity <= 0:
        # Remove item from cart
        cart = [item for item in cart if item['dish_id'] != dish_id]
    else:
        # Update quantity
        for item in cart:
            if item['dish_id'] == dish_id:
                item['quantity'] = quantity
                break
    
    session['cart'] = cart
    session.modified = True
    flash('Cart updated successfully', 'success')
    return redirect(url_for('customer_cart'))

@app.route('/customer/clear_cart')
@login_required
def clear_cart():
    session['cart'] = []
    flash('Cart cleared successfully', 'success')
    return redirect(url_for('customer_cart'))

@app.route('/customer/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('customer_cart'))
    
    if request.method == 'POST':
        try:
            # Calculate total price and prepare order items
            total_price = 0
            order_items = []
            
            for item in session['cart']:
                dish = db.dishes.find_one({'_id': ObjectId(item['dish_id'])})
                if not dish:
                    continue
                
                item_total = dish['Price'] * item['quantity']
                total_price += item_total
                
                order_items.append({
                    'DishID': dish['_id'],
                    'Quantity': item['quantity'],
                    'UnitPrice': dish['Price'],
                    'Subtotal': item_total
                })
            
            # Create order document
            order = {
                'CustomerID': ObjectId(session['user_id']),
                'OrderTime': datetime.now(),
                'OrderType': request.form.get('order_type', 'Delivery'),
                'OrderStatus': 'Pending',
                'PaymentType': request.form.get('payment_type', 'Cash'),
                'DeliveryAddress': request.form.get('delivery_address'),
                'ContactPhone': request.form.get('contact_phone'),
                'SpecialInstructions': request.form.get('special_instructions'),
                'TotalPrice': total_price,
                'Dishes': order_items,
                'LastUpdated': datetime.now()
            }
            
            # Insert order into database
            db.orders.insert_one(order)
            
            # Clear the cart
            session['cart'] = []
            flash('Order placed successfully! You can track your order in the orders section.', 'success')
            return redirect(url_for('customer_orders'))
            
        except Exception as e:
            flash(f'Error placing order: {str(e)}', 'error')
            return redirect(url_for('customer_cart'))
    
    return render_template('customer/checkout.html')

@app.route('/customer/orders')
@login_required
def customer_orders():
    # Updated pipeline to use consistent field names
    pipeline = [
        {
            '$match': {
                'customer_id': ObjectId(session['user_id'])
            }
        },
        {
            '$lookup': {
                'from': 'dishes',
                'localField': 'dishes.dish_id',
                'foreignField': '_id',
                'as': 'dish_details'
            }
        },
        {
            '$sort': {
                'order_time': -1
            }
        }
    ]
    
    orders = list(db.orders.aggregate(pipeline))
    return render_template('customer/orders.html', orders=orders)

@app.route('/customer/register-permanent', methods=['GET', 'POST'])
@login_required  # Ensures user is logged in
def register_permanent_customer():
    # Get current user's basic info
    current_user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    if request.method == 'POST':
        try:
            # Create permanent customer document
            permanent_customer = {
                'user_id': ObjectId(session['user_id']),
                'username': current_user['username'],
                'first_name': current_user['first_name'],
                'last_name': current_user['last_name'],
                'phone_number': current_user['phone_number'],
                
                # Additional details from form
                'email': request.form.get('email'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'state': request.form.get('state'),
                'postal_code': request.form.get('postal_code'),
                'diet_preference': request.form.get('diet_preference'),
                'allergies': request.form.getlist('allergies'),  # Multiple selections
                'preferred_payment_method': request.form.get('preferred_payment'),
                'special_instructions': request.form.get('special_instructions'),
                'birthday': datetime.strptime(request.form.get('birthday'), '%Y-%m-%d') if request.form.get('birthday') else None,
                'newsletters': 'subscribe_newsletter' in request.form,
                'loyalty_points': 0,  # Initialize loyalty points
                'membership_date': datetime.now(),
                'status': 'active'
            }
            
            # Check if user is already a permanent customer
            existing_customer = db.permanent_customers.find_one({'user_id': ObjectId(session['user_id'])})
            if existing_customer:
                flash('You are already registered as a permanent customer', 'info')
                return redirect(url_for('customer_menu'))
            
            # Insert into permanent_customers collection
            result = db.permanent_customers.insert_one(permanent_customer)
            
            if result.inserted_id:
                # Update user's role in the users collection
                db.users.update_one(
                    {'_id': ObjectId(session['user_id'])},
                    {
                        '$set': {
                            'is_permanent_customer': True,
                            'customer_id': result.inserted_id
                        }
                    }
                )
                
                flash('Successfully registered as a permanent customer!', 'success')
                return redirect(url_for('customer_menu'))
            else:
                flash('Error registering as permanent customer', 'error')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register_permanent_customer'))
    
    return render_template('customer/permanent_registration.html', user=current_user)


@app.route('/customer/place_order', methods=['POST'])
@login_required
def place_order():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty', 'error')
        return redirect(url_for('customer_cart'))
    
    try:
        # Calculate total price and prepare order items
        total_price = 0
        order_items = []
        
        for item in session['cart']:
            dish = db.dishes.find_one({'_id': ObjectId(item['dish_id'])})
            if not dish:
                continue
            
            item_total = dish['Price'] * item['quantity']
            total_price += item_total
            
            order_items.append({
                'dish_id': dish['_id'],
                'dish_name': dish['DishName'],
                'quantity': item['quantity'],
                'unit_price': dish['Price'],
                'subtotal': item_total
            })
        
        # Create order document with consistent field names
        order = {
            'customer_id': ObjectId(session['user_id']),
            'order_time': datetime.now(),
            'order_type': request.form.get('order_type', 'Delivery'),
            'status': 'Pending',
            'payment_type': request.form.get('payment_type', 'Cash'),
            'special_instructions': request.form.get('special_instructions'),
            'total_price': total_price,
            'dishes': order_items,
            'last_updated': datetime.now()
        }
        
        # Add delivery details if applicable
        if order['order_type'] == 'Delivery':
            order['delivery_address'] = request.form.get('delivery_address')
            order['contact_phone'] = request.form.get('contact_phone')
        
        # Insert order into database
        result = db.orders.insert_one(order)
        
        if result.inserted_id:
            session['cart'] = []
            flash('Order placed successfully! You can track your order in the orders section.', 'success')
            return redirect(url_for('customer_orders'))
        else:
            flash('Error placing order. Please try again.', 'error')
            return redirect(url_for('customer_cart'))
            
    except Exception as e:
        flash(f'Error placing order: {str(e)}', 'error')
        return redirect(url_for('customer_cart'))

@app.route('/customer/order/<order_id>')
@login_required
def order_detail(order_id):
    # Updated pipeline with consistent field names
    pipeline = [
        {
            '$match': {
                '_id': ObjectId(order_id),
                'customer_id': ObjectId(session['user_id'])
            }
        },
        {
            '$lookup': {
                'from': 'dishes',
                'localField': 'dishes.dish_id',
                'foreignField': '_id',
                'as': 'dish_details'
            }
        }
    ]
    
    order = list(db.orders.aggregate(pipeline))
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('customer_orders'))
    
    return render_template('customer/order_detail.html', order=order[0])

# Update the template to match the new field names
@app.template_filter('format_order_date')
def format_order_date(date):
    """Format datetime object to readable string"""
    if isinstance(date, datetime):
        return date.strftime('%B %d, %Y %I:%M %p')
    return date
    
@app.route('/profile')
@login_required
def profile():
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    return render_template('profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = db.users.find_one({'_id': ObjectId(session['user_id'])})
    
    if request.method == 'POST':
        try:
            updates = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'phone_number': request.form.get('phone_number'),
                'email': request.form.get('email'),
                'last_modified': datetime.now()
            }
            
            # Handle password update if provided
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            if current_password and new_password:
                if not check_password_hash(user['password'], current_password):
                    flash('Current password is incorrect', 'error')
                    return redirect(url_for('edit_profile'))
                updates['password'] = generate_password_hash(new_password)
            
            db.users.update_one(
                {'_id': ObjectId(session['user_id'])},
                {'$set': updates}
            )
            
            flash('Profile updated successfully', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('edit_profile.html', user=user)

# Add route for canceling orders
@app.route('/customer/cancel-order/<order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    try:
        # Verify the order belongs to the current user
        order = db.orders.find_one({
            '_id': ObjectId(order_id),
            'CustomerID': ObjectId(session['user_id'])
        })
        
        if not order:
            flash('Order not found', 'error')
            return redirect(url_for('order_history'))
            
        if order['OrderStatus'] != 'Pending':
            flash('Only pending orders can be cancelled', 'error')
            return redirect(url_for('order_history'))
        
        # Update order status to Cancelled
        db.orders.update_one(
            {'_id': ObjectId(order_id)},
            {
                '$set': {
                    'OrderStatus': 'Cancelled',
                    'LastUpdated': datetime.now()
                }
            }
        )
        
        flash('Order cancelled successfully', 'success')
        
    except Exception as e:
        flash(f'Error cancelling order: {str(e)}', 'error')
        
    return redirect(url_for('order_history'))

# Add to your Flask routes
@app.route('/customer/order-history')
@login_required
def order_history():
    try:
        # Updated pipeline with correct field names
        pipeline = [
            {
                '$match': {
                    'customer_id': ObjectId(session['user_id'])
                }
            },
            {
                '$lookup': {
                    'from': 'dishes',
                    'localField': 'dishes.dish_id',
                    'foreignField': '_id',
                    'as': 'dish_details'
                }
            },
            {
                '$sort': {
                    'order_time': -1
                }
            }
        ]
        
        orders = list(db.orders.aggregate(pipeline))
        return render_template('customer/order_history.html', orders=orders)
    except Exception as e:
        flash(f'Error retrieving order history: {str(e)}', 'error')
        return redirect(url_for('customer_menu'))
    
@app.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form['username']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            # Validate passwords match
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('register_customer'))
            
            # Check if username already exists
            if db.users.find_one({'username': username}):
                flash('Username already exists', 'error')
                return redirect(url_for('register_customer'))
            
            # Get allergies as list
            allergies = request.form.getlist('allergies')
            
            # Create user document
            user = {
                'username': username,
                'password': generate_password_hash(password),
                'role': 'customer',
                'first_name': request.form['first_name'],
                'last_name': request.form['last_name'],
                'phone_number': request.form['phone_number'],
                'dob': datetime.strptime(request.form['dob'], '%Y-%m-%d'),
                'diet_preference': request.form['diet_preference'],
                'allergies': allergies,
                'registration_date': datetime.now()
            }
            
            # Insert into database
            result = db.users.insert_one(user)
            
            if result.inserted_id:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error during registration', 'error')
                
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(url_for('register_customer'))
            
    return render_template('customer/register.html')
from flask import Flask, request, jsonify, render_template, flash, redirect, url_for, session
from functools import wraps
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json
from typing import Dict, List, Any, Optional

class RestaurantAdminChatbot:
    def __init__(self):
        self.llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="mixtral-8x7b-32768"
        )
        
        self.collections = {
            'users': db.users,
            'dishes': db.dishes,
            'orders': db.orders,
            'ingredients': db.ingredients,
            'employees': db.employees,
            'permanent_customers': db.permanent_customers
        }
        
        self.system_prompt = ChatPromptTemplate.from_template("""
            You are an AI assistant for a restaurant management system.
            Use the following rules to process queries and provide responses:
            
            1. For data queries, use the MongoDB collections data provided
            2. For analytical questions, combine data with business insights
            3. Always provide clear, structured responses
            4. If data is missing, explain what information would be needed
            
            Current collections in database:
            - users: User accounts and profiles
            - dishes: Menu items and details
            - orders: Customer orders and status
            - ingredients: Inventory and stock
            - employees: Staff information
            - permanent_customers: Regular customer data
            
            Context: {context}
            Question: {query}
        """)

    def get_mongodb_data(self, query_type: str, filters: Dict = None) -> Dict:
        try:
            if filters is None:
                filters = {}

            if query_type == "menu":
                return list(self.collections['dishes'].find(filters))
            elif query_type == "orders":
                return list(self.collections['orders'].find(filters))
            elif query_type == "inventory":
                return list(self.collections['ingredients'].find(filters))
            elif query_type == "employees":
                return list(self.collections['employees'].find(filters))
            elif query_type == "customers":
                return list(self.collections['permanent_customers'].find(filters))
            else:
                return []
        except Exception as e:
            print(f"Database error: {str(e)}")
            return []

    def analyze_query(self, query: str) -> tuple:
        query_lower = query.lower()
        
        patterns = {
            'menu': ['menu', 'dish', 'food', 'price'],
            'orders': ['order', 'delivery', 'pickup', 'sales'],
            'inventory': ['inventory', 'stock', 'ingredient', 'supply'],
            'employees': ['employee', 'staff', 'worker', 'schedule'],
            'customers': ['customer', 'client', 'patron', 'loyalty']
        }
        
        for query_type, keywords in patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return query_type, self.extract_filters(query_lower)
        
        return 'general', {}

    def extract_filters(self, query: str) -> Dict:
        filters = {}
        
        if 'today' in query:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            filters['date'] = {'$gte': today}
        
        if 'available' in query:
            filters['IsAvailable'] = True
        if 'out of stock' in query:
            filters['QuantityInStock'] = 0
        
        if 'vegetarian' in query:
            filters['Category'] = 'Vegetarian'
        if 'delivery' in query:
            filters['order_type'] = 'Delivery'
        
        return filters

    def process_query(self, user_query: str) -> str:
        try:
            if user_query.startswith('db:'):
                return self.handle_db_command(user_query)
            
            query_type, filters = self.analyze_query(user_query)
            context_data = self.get_mongodb_data(query_type, filters)
            
            context = f"""
            Query Type: {query_type}
            Available Data: {json.dumps(context_data, default=str)}
            """
            
            messages = self.system_prompt.format_messages(
                context=context,
                query=user_query
            )
            response = self.llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def handle_db_command(self, command: str) -> str:
        try:
            parts = command.split(" ")
            operation = parts[1]
            collection_name = parts[2]
            
            if collection_name not in self.collections:
                return f"Invalid collection. Available collections: {', '.join(self.collections.keys())}"
            
            collection = self.collections[collection_name]
            
            if operation == "find":
                query = eval(" ".join(parts[3:])) if len(parts) > 3 else {}
                results = list(collection.find(query))
                return f"Found {len(results)} documents:\n" + "\n".join(str(doc) for doc in results)
            
            elif operation == "count":
                query = eval(" ".join(parts[3:])) if len(parts) > 3 else {}
                count = collection.count_documents(query)
                return f"Count: {count} documents"
            
            return "Invalid operation"
            
        except Exception as e:
            return f"Error executing database command: {str(e)}"

# Initialize chatbot
chatbot = RestaurantAdminChatbot()
# ... (previous code remains the same until the routes section)

# Add this new route for the admin chatbot interface
@app.route('/admin/chatbot')
@login_required
@admin_required
def admin_chatbot():
    return render_template('admin/chatbot.html')

# Add the chatbot API endpoint specifically for admin use
@app.route('/admin/chat', methods=['POST'])
@login_required
@admin_required
def admin_chat():
    try:
        data = request.json
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'Query is required'}), 400
        
        response = chatbot.process_query(user_query)
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create the chatbot HTML template file: templates/admin/chatbot.html
@app.route('/admin/chatbot/template')
def get_chatbot_template():
    return render_template('admin/chatbot.html')

# ... (rest of the previous code remains the same)
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500


# Initialize the database when the app starts
init_db()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
