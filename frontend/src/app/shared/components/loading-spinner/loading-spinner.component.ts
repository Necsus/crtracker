/* ============================================
   LOADING SPINNER COMPONENT
   Displays a loading indicator
   ============================================ */

import { Component, input } from '@angular/core';

/**
 * Loading Spinner Component - Dumb/presentational component
 *
 * Displays:
 * - Animated spinner
 * - Optional message
 */
@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  templateUrl: './loading-spinner.component.html',
  styleUrl: './loading-spinner.component.scss',
})
export class LoadingSpinnerComponent {
  /** Size variant */
  readonly size = input<'sm' | 'md' | 'lg'>('md');

  /** Optional loading message */
  readonly message = input<string>('');

  /** Whether to show overlay */
  readonly overlay = input(false);
}
