import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly THEME_KEY = 'rag_app_theme';
  private isDarkTheme = new BehaviorSubject<boolean>(true);
  
  isDarkTheme$ = this.isDarkTheme.asObservable();

  constructor() {
    this.initTheme();
  }

  private initTheme() {
    const savedTheme = localStorage.getItem(this.THEME_KEY);
    if (savedTheme) {
      const isDark = savedTheme === 'dark';
      this.isDarkTheme.next(isDark);
      this.applyTheme(isDark);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.isDarkTheme.next(prefersDark);
      this.applyTheme(prefersDark);
    }
  }

  toggleTheme() {
    const newValue = !this.isDarkTheme.value;
    this.isDarkTheme.next(newValue);
    this.applyTheme(newValue);
    localStorage.setItem(this.THEME_KEY, newValue ? 'dark' : 'light');
  }

  private applyTheme(isDark: boolean) {
    if (isDark) {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    }
  }
}
