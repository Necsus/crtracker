/* ============================================
   API INTERCEPTOR
   Handles HTTP requests/responses with base URL and error handling
   ============================================ */

import { HttpEvent, HttpHandlerFn, HttpRequest } from '@angular/common/http';
import { Observable, throwError, timer } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';
import { environment } from '../../environments/environment';

/**
 * Maximum retry attempts for failed requests
 */
const MAX_RETRIES = 2;

/**
 * API Interceptor for HTTP requests
 *
 * Functions:
 * - Adds base URL to relative URLs
 * - Adds authentication headers (when implemented)
 * - Handles errors with user-friendly messages
 * - Implements retry logic for transient failures
 */
export const apiInterceptor = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn,
): Observable<HttpEvent<unknown>> => {
  // Add base URL to relative paths
  const apiUrl = req.url.startsWith('http')
    ? req.url
    : `${environment.apiBaseUrl}${req.url}`;

  // Clone request with modified URL and headers
  const apiReq = req.clone({
    url: apiUrl,
    setHeaders: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  });

  // Send request and handle response/errors
  return next(apiReq).pipe(
    // Retry logic with exponential backoff (replaces deprecated retryWhen)
    retry({
      count: MAX_RETRIES,
      delay: (error, retryIndex) => {
        // Don't retry client errors (4xx)
        if (error.status >= 400 && error.status < 500) {
          throw error;
        }
        const backoffTime = Math.pow(2, retryIndex) * 1000;
        return timer(backoffTime);
      },
    }),
    // Error handling
    catchError((error) => {
      // User-friendly error messages
      let userMessage = 'An unexpected error occurred. Please try again.';

      if (error.status === 0) {
        userMessage = 'Unable to connect to the server. Please check your connection.';
      } else if (error.status === 404) {
        userMessage = 'The requested resource was not found.';
      } else if (error.status === 500) {
        userMessage = 'Server error. Our team has been notified.';
      }

      return throwError(() => ({
        ...error,
        userMessage,
      }));
    })
  );
};

/**
 * Construct URL with query parameters
 */
export function buildUrl(baseUrl: string, params: Record<string, string | number | boolean | undefined>): string {
  const queryParams = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');

  return queryParams ? `${baseUrl}?${queryParams}` : baseUrl;
}
