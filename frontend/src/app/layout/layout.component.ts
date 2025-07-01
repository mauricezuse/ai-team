import { Component } from '@angular/core';
import { MenubarModule } from 'primeng/menubar';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [MenubarModule, RouterOutlet],
  templateUrl: './layout.component.html',
  styleUrl: './layout.component.scss'
})
export class LayoutComponent {
  menuItems = [
    { label: 'Dashboard', icon: 'pi pi-home', routerLink: '/dashboard' },
    { label: 'Agents', icon: 'pi pi-users', routerLink: '/agents' },
    { label: 'Workflows', icon: 'pi pi-sitemap', routerLink: '/workflows' }
  ];
}
