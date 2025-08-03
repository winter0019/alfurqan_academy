// main.js

// Firebase Configuration
// You MUST replace this with your project's configuration object.
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};

// Initialize Firebase
const app = firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

// UI Elements
const authContainer = document.getElementById('auth-container');
const dashboardContainer = document.getElementById('dashboard-container');
const userDashboardContent = document.getElementById('user-dashboard-content');
const adminDashboardContent = document.getElementById('admin-dashboard-content');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const showRegisterBtn = document.getElementById('show-register');
const showLoginBtn = document.getElementById('show-login');
const logoutBtn = document.getElementById('logout-btn');
const userEmailSpan = document.getElementById('user-email');
const addStudentForm = document.getElementById('add-student-form');
const studentsList = document.getElementById('students-list');

// --- Authentication UI Handlers ---
showRegisterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
});

showLoginBtn.addEventListener('click', (e) => {
    e.preventDefault();
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
});

// --- Authentication Logic ---

// Register User
registerForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = registerForm['register-email'].value;
    const password = registerForm['register-password'].value;

    auth.createUserWithEmailAndPassword(email, password)
        .then((cred) => {
            // After successful registration, create a user profile in Firestore
            return db.collection('users').doc(cred.user.uid).set({
                email: email,
                role: 'user' // Default role is 'user'
            });
        })
        .then(() => {
            alert('Registration successful! Please log in.');
            registerForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
        })
        .catch((error) => {
            alert(error.message);
        });
});

// Login User
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = loginForm['login-email'].value;
    const password = loginForm['login-password'].value;

    auth.signInWithEmailAndPassword(email, password)
        .catch((error) => {
            alert(error.message);
        });
});

// Logout User
logoutBtn.addEventListener('click', () => {
    auth.signOut().then(() => {
        console.log('User logged out');
    });
});

// Auth State Listener
auth.onAuthStateChanged(user => {
    if (user) {
        // User is signed in. Fetch their role from Firestore.
        db.collection('users').doc(user.uid).get()
            .then(doc => {
                if (doc.exists) {
                    const userData = doc.data();
                    const role = userData.role;
                    userEmailSpan.textContent = user.email + ` (${role})`;

                    // Show the correct dashboard based on the user's role
                    authContainer.classList.add('hidden');
                    dashboardContainer.classList.remove('hidden');

                    if (role === 'admin') {
                        userDashboardContent.classList.add('hidden');
                        adminDashboardContent.classList.remove('hidden');
                        // You can add logic for the admin dashboard here
                    } else {
                        adminDashboardContent.classList.add('hidden');
                        userDashboardContent.classList.remove('hidden');
                        getStudents(user.uid);
                    }
                }
            })
            .catch(error => {
                console.error("Error getting user role:", error);
                auth.signOut(); // Log them out if their user data is not found
            });
    } else {
        // User is signed out
        authContainer.classList.remove('hidden');
        dashboardContainer.classList.add('hidden');
        studentsList.innerHTML = '';
        userDashboardContent.classList.remove('hidden');
        adminDashboardContent.classList.add('hidden');
    }
});

// --- Firestore Database Logic ---

// Add a new student
addStudentForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const user = auth.currentUser;
    if (!user) return;

    const newStudent = {
        firstName: addStudentForm['first-name'].value,
        lastName: addStudentForm['last-name'].value,
        enrollmentDate: addStudentForm['enrollment-date'].value,
        createdAt: firebase.firestore.FieldValue.serverTimestamp()
    };

    db.collection(`users/${user.uid}/students`).add(newStudent)
        .then(() => {
            addStudentForm.reset();
        })
        .catch((error) => {
            alert("Error adding student: " + error.message);
        });
});

// Get students and listen for real-time changes
function getStudents(userId) {
    db.collection(`users/${userId}/students`).orderBy('createdAt', 'desc')
        .onSnapshot((snapshot) => {
            studentsList.innerHTML = ''; // Clear the list
            snapshot.forEach((doc) => {
                const student = doc.data();
                const studentItem = document.createElement('li');
                studentItem.className = 'flex justify-between items-center bg-gray-50 p-4 rounded-md shadow';
                studentItem.innerHTML = `
                    <div>
                        <p class="font-semibold">${student.firstName} ${student.lastName}</p>
                        <p class="text-sm text-gray-600">Enrolled: ${student.enrollmentDate}</p>
                    </div>
                    <div class="flex space-x-2">
                        <button data-id="${doc.id}" class="edit-btn text-blue-500 hover:text-blue-700">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button data-id="${doc.id}" class="delete-btn text-red-500 hover:text-red-700">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
                studentsList.appendChild(studentItem);
            });
        });
}

// Handle delete and edit buttons
studentsList.addEventListener('click', (e) => {
    const user = auth.currentUser;
    if (!user) return;

    const target = e.target.closest('button');
    if (!target) return;

    const docId = target.dataset.id;

    if (target.classList.contains('delete-btn')) {
        if (confirm('Are you sure you want to delete this student?')) {
            db.collection(`users/${user.uid}/students`).doc(docId).delete()
                .catch((error) => {
                    alert("Error removing student: " + error.message);
                });
        }
    } else if (target.classList.contains('edit-btn')) {
        // TODO: Implement edit functionality
        alert('Edit functionality not yet implemented.');
    }
});

// Add Admin Data Button (example)
document.getElementById('add-admin-data-btn').addEventListener('click', () => {
    db.collection('admin_data').add({
        message: "This is a secret message for admins!",
        createdAt: firebase.firestore.FieldValue.serverTimestamp()
    })
    .then(() => {
        alert("Admin data added successfully!");
    })
    .catch((error) => {
        alert("Error adding admin data: " + error.message);
    });
});
