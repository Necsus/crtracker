/* CRTracker Main Entry Point */

import { bootstrapApplication } from '@angular/platform-browser';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { AppComponent } from './app/app.component';
import { appConfig } from './app/app.config';

/* Bootstrap the Angular application with required providers */
bootstrapApplication(AppComponent, {
  ...appConfig,
  providers: [
    ...(appConfig.providers || []),
    provideAnimationsAsync(),
  ],
}).catch((err) => console.error('Application bootstrap error:', err));
