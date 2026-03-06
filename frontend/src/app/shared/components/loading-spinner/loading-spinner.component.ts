/* ============================================
   LOADING SPINNER COMPONENT
   Displays a loading indicator
   ============================================ */

import { NgClass } from '@angular/common';
import { Component, computed, input } from '@angular/core';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [NgClass],
  templateUrl: './loading-spinner.component.html',
})
export class LoadingSpinnerComponent {
  readonly size = input<'sm' | 'md' | 'lg'>('md');
  readonly message = input<string>('');
  readonly overlay = input(false);

  readonly spinnerSizeClass = computed(() =>
    ({ sm: 'w-6 h-6', md: 'w-10 h-10', lg: 'w-16 h-16' })[this.size()] ?? 'w-10 h-10'
  );
}
