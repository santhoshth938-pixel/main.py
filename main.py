import sqlite3
import os
from flask import Flask, jsonify, request, render_template_string

# ---------------------------------------------------------
# 1. FLASK APPLICATION & DATABASE SETUP
# ---------------------------------------------------------
app = Flask(__name__)
DB_NAME = "database.db"

def setup_database():
    """Creates the database table and populates 3 sample items automatically."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            location TEXT NOT NULL,
            secret_prompt TEXT NOT NULL,
            secret_answer TEXT NOT NULL,
            contact TEXT NOT NULL
        )
    ''')
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        # Pre-load sample data if database is empty
        sample_items = [
            ("Scientific Calculator FX-991EX", "Electronics", "Central Lab Floor 2", "What name is written on the back?", "rahul", "9876543210"),
            ("College ID Card", "IDs & Cards", "Canteen Block A", "What branch/department is listed?", "cse", "9123456789"),
            ("Honda Bike Keys", "Keys", "Parking Lot Gate 2", "What color keychain is attached?", "red", "9988776655")
        ]
        cursor.executemany('''
            INSERT INTO items (title, category, location, secret_prompt, secret_answer, contact)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', sample_items)
        conn.commit()
        print("Database successfully created with 3 sample lost items!")
        
    conn.close()

# ---------------------------------------------------------
# 2. WEB PAGE DESIGN (HTML + JavaScript inline)
# ---------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Campus Lost & Found Portal</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-light">

  <nav class="navbar navbar-dark bg-primary shadow-sm mb-4">
    <div class="container">
      <a class="navbar-brand fw-bold" href="#"><i class="fas fa-search-location me-2"></i>Campus Lost & Found</a>
      <button class="btn btn-light fw-semibold" data-bs-toggle="modal" data-bs-target="#postModal">
        <i class="fas fa-plus-circle me-1"></i> Report Found Item
      </button>
    </div>
  </nav>

  <div class="container">
    <h3 class="mb-3 text-center">Reported Found Items</h3>
    <div id="itemsContainer" class="row g-4"></div>
  </div>

  <!-- Modal: Report Item -->
  <div class="modal fade" id="postModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title">Report Found Item</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <form id="postForm">
            <input type="text" name="title" class="form-control mb-2" placeholder="Item Title (e.g. Water Bottle)" required>
            <select name="category" class="form-select mb-2" required>
              <option value="Electronics">Electronics</option>
              <option value="IDs & Cards">IDs & Cards</option>
              <option value="Keys">Keys</option>
              <option value="Other">Other</option>
            </select>
            <input type="text" name="location" class="form-control mb-2" placeholder="Location Found (e.g. Library)" required>
            <input type="text" name="secret_prompt" class="form-control mb-2" placeholder="Secret Question (e.g. Color of cap?)" required>
            <input type="text" name="secret_answer" class="form-control mb-2" placeholder="Secret Answer (e.g. Blue)" required>
            <input type="text" name="contact" class="form-control mb-2" placeholder="Your Phone Number" required>
            <button type="submit" class="btn btn-success w-100 mt-2">Submit</button>
          </form>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal: Claim Verification -->
  <div class="modal fade" id="claimModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header bg-warning">
          <h5 class="modal-title">Ownership Verification</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
        </div>
        <div class="modal-body">
          <input type="hidden" id="claimItemId">
          <p class="fw-bold" id="claimPromptText"></p>
          <input type="text" id="claimAnswerInput" class="form-control mb-3" placeholder="Type your answer...">
          <button class="btn btn-primary w-100" onclick="submitClaim()">Verify & Claim</button>
          <div id="claimResult" class="mt-3"></div>
        </div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    async function fetchItems() {
      const res = await fetch('/api/items');
      const items = await res.json();
      const container = document.getElementById('itemsContainer');
      container.innerHTML = '';

      items.forEach(item => {
        container.innerHTML += `
          <div class="col-md-4">
            <div class="card h-100 shadow-sm p-3">
              <span class="badge bg-info text-dark w-50 mb-2">${item.category}</span>
              <h5>${item.title}</h5>
              <p class="text-muted"><i class="fas fa-map-marker-alt"></i> ${item.location}</p>
              <button class="btn btn-outline-primary mt-auto" onclick="openClaimModal(${item.id}, '${item.secret_prompt}')">
                <i class="fas fa-key"></i> Claim Item
              </button>
            </div>
          </div>
        `;
      });
    }

    document.getElementById('postForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      await fetch('/api/post-item', { method: 'POST', body: formData });
      bootstrap.Modal.getInstance(document.getElementById('postModal')).hide();
      e.target.reset();
      fetchItems();
    });

    function openClaimModal(id, promptText) {
      document.getElementById('claimItemId').value = id;
      document.getElementById('claimPromptText').innerText = "Question: " + promptText;
      document.getElementById('claimAnswerInput').value = '';
      document.getElementById('claimResult').innerHTML = '';
      new bootstrap.Modal(document.getElementById('claimModal')).show();
    }

    async function submitClaim() {
      const id = document.getElementById('claimItemId').value;
      const answer = document.getElementById('claimAnswerInput').value;

      const res = await fetch('/api/verify-claim', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id, answer: answer })
      });
      const data = await res.json();

      const resultDiv = document.getElementById('claimResult');
      if (data.success) {
        resultDiv.innerHTML = `<div class="alert alert-success">Verified! Founder Contact: <strong>${data.contact}</strong></div>`;
      } else {
        resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
      }
    }

    fetchItems();
  </script>
</body>
</html>
"""

# ---------------------------------------------------------
# 3. API ENDPOINTS & ROUTES
# ---------------------------------------------------------
@app.route('/')
def home():
    """Serves the web page directly."""
    return render_template_string(HTML_PAGE)

@app.route('/api/items', methods=['GET'])
def get_items():
    """Fetches all items from SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, location, secret_prompt FROM items ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    items = [{"id": r[0], "title": r[1], "category": r[2], "location": r[3], "secret_prompt": r[4]} for r in rows]
    return jsonify(items)

@app.route('/api/post-item', methods=['POST'])
def post_item():
    """Saves a newly reported item into SQLite database."""
    d = request.form
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO items (title, category, location, secret_prompt, secret_answer, contact)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (d['title'], d['category'], d['location'], d['secret_prompt'], d['secret_answer'].lower().strip(), d['contact']))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/verify-claim', methods=['POST'])
def verify_claim():
    """Verifies user answer against the true answer in SQLite database."""
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT secret_answer, contact FROM items WHERE id = ?", (data['id'],))
    row = cursor.fetchone()
    conn.close()

    if row and row[0] == data['answer'].lower().strip():
        return jsonify({"success": True, "contact": row[1]})
    else:
        return jsonify({"success": False, "message": "Incorrect answer! Access denied."})

# ---------------------------------------------------------
# 4. RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    setup_database()
    app.run(debug=True, port=5000)