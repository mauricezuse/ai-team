import { Injectable, inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';

@Injectable({ providedIn: 'root' })
export class FeatureFlagService {
  private doc = inject(DOCUMENT);

  // Flags are read from <meta name="ai-team-flags" content="KEY1=1,KEY2=0"> or window.__AI_FLAGS__
  isEnabled(key: string, defaultValue = false): boolean {
    const globalFlags = (window as any).__AI_FLAGS__ as Record<string, string> | undefined;
    const meta = this.doc.querySelector('meta[name="ai-team-flags"]') as HTMLMetaElement | null;
    const truthy = new Set(['1', 'true', 'yes', 'on']);
    const upper = key.toUpperCase();

    if (globalFlags && upper in globalFlags) {
      return truthy.has(String(globalFlags[upper]).toLowerCase());
    }
    if (meta?.content) {
      const pairs = meta.content.split(',').map(v => v.trim());
      for (const p of pairs) {
        const [k, v] = p.split('=');
        if (k?.toUpperCase() === upper) {
          return truthy.has(String(v).toLowerCase());
        }
      }
    }
    return defaultValue;
  }
}


