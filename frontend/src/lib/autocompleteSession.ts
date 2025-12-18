/**
 * Autocomplete Session Token Manager
 * 
 * Manages session tokens for Google Places Autocomplete API to optimize costs.
 * 
 * WITHOUT proper session tokens: $0.017 per keystroke
 * WITH session tokens: $0.017 per complete selection
 * 
 * Savings: ~92% reduction in autocomplete API costs
 * 
 * @see backend/docs/AUTOCOMPLETE_SESSION_TOKEN_GUIDE.md
 */

class AutocompleteSessionManager {
  private currentToken: string | null = null;
  private requestCount: number = 0;
  private sessionStartTime: number | null = null;

  /**
   * Start a new autocomplete session
   * Call this when user focuses on search input
   * 
   * @returns {string} New session token
   */
  startSession(): string {
    // Generate UUID v4 compatible token
    this.currentToken = this.generateUUID();
    this.requestCount = 0;
    this.sessionStartTime = Date.now();
    
    console.log('🎫 Started autocomplete session:', this.currentToken);
    
    return this.currentToken;
  }

  /**
   * Get current active session token
   * 
   * @returns {string | null} Current token or null if no active session
   */
  getToken(): string | null {
    return this.currentToken;
  }

  /**
   * Increment request counter for tracking
   * Call this each time autocomplete API is called
   */
  incrementRequestCount(): void {
    this.requestCount++;
  }

  /**
   * End current session and clear token
   * Call this after user selects a place or cancels search
   */
  endSession(): void {
    if (!this.currentToken) {
      return;
    }

    const duration = this.sessionStartTime 
      ? (Date.now() - this.sessionStartTime) / 1000 
      : 0;

    console.log(
      `🎫 Ended autocomplete session: ${this.currentToken} ` +
      `(${this.requestCount} requests, ${duration.toFixed(1)}s duration)`
    );

    // Calculate cost savings
    const estimatedCost = 0.017; // Only 1 billable session
    const savedCost = (this.requestCount - 1) * 0.017;
    
    if (this.requestCount > 1) {
      console.log(
        `💰 Saved $${savedCost.toFixed(3)} ` +
        `(${this.requestCount} requests → 1 billable session)`
      );
    }

    this.currentToken = null;
    this.requestCount = 0;
    this.sessionStartTime = null;
  }

  /**
   * Check if there's an active session
   * 
   * @returns {boolean} True if session is active
   */
  hasActiveSession(): boolean {
    return this.currentToken !== null;
  }

  /**
   * Force start a new session (ends current if active)
   * 
   * @returns {string} New session token
   */
  restartSession(): string {
    if (this.hasActiveSession()) {
      this.endSession();
    }
    return this.startSession();
  }

  /**
   * Generate UUID v4 compatible token
   * Falls back to crypto.randomUUID() if available
   * 
   * @private
   * @returns {string} UUID string
   */
  private generateUUID(): string {
    // Use crypto.randomUUID if available (modern browsers)
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }

    // Fallback: Generate UUID v4 manually
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}

// Export singleton instance
export const autocompleteSession = new AutocompleteSessionManager();
