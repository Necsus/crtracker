import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { apiInterceptor } from './00_dal/api.interceptor';
import { appRoutes } from './app.routes';

/**
 * Root application configuration
 *
 * Provides:
 * - Router with component input binding
 * - HTTP client with functional interceptor
 */
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(appRoutes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([apiInterceptor])),
  ],
};
