/**
 * Frontend validation utilities to match backend requirements
 */

export interface ValidationErrors {
  username?: string;
  email?: string;
  password?: string;
  authorize?: string;
}

/**
 * Validate email format
 * Backend uses EmailStr from Pydantic which is quite strict
 */
export const validateEmail = (email: string): string | null => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!email) {
    return "Email is required";
  }

  if (!emailRegex.test(email)) {
    return "Please enter a valid email address (e.g., user@example.com)";
  }

  if (email.length > 254) {
    return "Email is too long";
  }

  return null;
};

/**
 * Validate username
 * Backend: min_length=1, max_length=100, cannot be empty or whitespace
 */
export const validateUsername = (username: string): string | null => {
  if (!username) {
    return "Username is required";
  }

  if (username.trim().length === 0) {
    return "Username cannot be empty or whitespace";
  }

  if (username.length > 100) {
    return "Username must be less than 100 characters";
  }

  return null;
};

/**
 * Validate password strength
 * Backend: min_length=6
 */
export const validatePassword = (password: string): string | null => {
  if (!password) {
    return "Password is required";
  }

  if (password.length < 6) {
    return "Password must be at least 6 characters long";
  }

  if (password.trim() === "") {
    return "Password cannot be empty or whitespace";
  }

  return null;
};

/**
 * Validate password confirmation
 */
export const validatePasswordMatch = (
  password: string,
  confirm: string
): string | null => {
  if (!confirm) {
    return "Please confirm your password";
  }

  if (password !== confirm) {
    return "Passwords do not match";
  }

  return null;
};

/**
 * Validate signup form
 */
export const validateSignupForm = (data: {
  username: string;
  email: string;
  password: string;
  authorize: string;
}): ValidationErrors => {
  const errors: ValidationErrors = {};

  const usernameError = validateUsername(data.username);
  if (usernameError) errors.username = usernameError;

  const emailError = validateEmail(data.email);
  if (emailError) errors.email = emailError;

  const passwordError = validatePassword(data.password);
  if (passwordError) errors.password = passwordError;

  const matchError = validatePasswordMatch(data.password, data.authorize);
  if (matchError) errors.authorize = matchError;

  return errors;
};

/**
 * Validate login form
 */
export const validateLoginForm = (data: {
  email: string;
  password: string;
}): Pick<ValidationErrors, "email" | "password"> => {
  const errors: Pick<ValidationErrors, "email" | "password"> = {};

  const emailError = validateEmail(data.email);
  if (emailError) errors.email = emailError;

  const passwordError = validatePassword(data.password);
  if (passwordError) errors.password = passwordError;

  return errors;
};

/**
 * Get user-friendly error message for backend errors
 */
export const getFriendlyErrorMessage = (error: any): string => {
  if (typeof error === "string") return error;

  if (error.message) {
    // Handle specific backend error messages
    if (error.message.includes("email")) {
      return "Email is invalid or already in use";
    }
    if (error.message.includes("password")) {
      return "Password does not meet requirements";
    }
    if (error.message.includes("username")) {
      return "Username is invalid or already taken";
    }
    return error.message;
  }

  return "An error occurred. Please try again.";
};
