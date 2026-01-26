# Wallet System Frontend

A modern, beautiful React application for the Wallet System API.

## Features

- 🔐 **Authentication**: Secure login and signup
- 💰 **Wallet Dashboard**: View your balance in real-time
- 💸 **Send Money**: Transfer funds to other users
- 📊 **Transaction History**: Track all your transactions
- 🔒 **Idempotency**: Auto-generated UUIDs prevent duplicate transactions
- 🎨 **Modern UI**: Beautiful interface with Tailwind CSS

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool (faster than CRA)
- **Tailwind CSS** - Styling
- **Axios** - API calls
- **React Router** - Navigation

## Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Development Server
```bash
npm run dev
```

The app will open at `http://localhost:5173`

### 3. Make sure the backend is running
```bash
cd ..
uvicorn app.main:app --reload
```

Backend should be running at `http://127.0.0.1:8000`

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── api.js                 # API calls & UUID generation
│   ├── components/
│   │   ├── Dashboard.jsx          # Main dashboard
│   │   ├── Login.jsx              # Login form
│   │   ├── Signup.jsx             # Signup form
│   │   ├── TransferModal.jsx      # Send money modal
│   │   └── TransactionHistory.jsx # Transaction list
│   ├── context/
│   │   └── AuthContext.jsx        # Auth state management
│   ├── App.jsx                    # Main app with routing
│   ├── main.jsx                   # Entry point
│   └── index.css                  # Global styles
├── index.html
├── package.json
├── tailwind.config.js
└── vite.config.js
```

## Key Features Explained

### Automatic UUID Generation

The idempotency key is automatically generated in `api.js`:

```javascript
export const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};
```

Every transfer automatically gets a unique UUID - no manual input needed!

### Protected Routes

- **Public routes** (/, /login, /signup): Only accessible when logged out
- **Protected routes** (/dashboard): Only accessible when logged in
- Auto-redirect based on auth state

### Token Management

- Token stored in localStorage
- Automatically added to API requests
- Persists across page refreshes

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment

The app connects to:
- **Backend API**: `http://127.0.0.1:8000`
- **Frontend Dev Server**: `http://localhost:5173`

## Building for Production

```bash
npm run build
```

The build folder will contain optimized production files.

---

Built with ❤️ using React + Vite + Tailwind CSS
