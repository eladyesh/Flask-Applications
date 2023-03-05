from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# A list to hold our todo items
todo_list = []

# Route to handle the home page
@app.route('/')
def index():
    return render_template('index.html', todo_list=todo_list)

# Route to handle adding a new todo item
@app.route('/add', methods=['POST'])
def add():
    # Get the new todo item from the form
    new_todo = request.form['new-todo']
    # Add the new todo item to the list
    todo_list.append(new_todo)
    # Redirect back to the home page
    return redirect(url_for('index'))

# Route to handle deleting a todo item
@app.route('/delete/<int:index>')
def delete(index):
    # Remove the todo item from the list
    todo_list.pop(index)
    # Redirect back to the home page
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
