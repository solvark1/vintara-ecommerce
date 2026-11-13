<?php
/*
  $Id$

  CE Phoenix, E-Commerce made Easy
  https://phoenixcart.org

  Copyright (c) 2024 Phoenix Cart

  Released under the GNU General Public License
*/

  const MODULE_NAVBAR_ACCOUNT_TITLE = 'Mi cuenta';
  const MODULE_NAVBAR_ACCOUNT_DESCRIPTION = 'Show Customer Mi cuenta Actions in Navbar.';

  const MODULE_NAVBAR_ACCOUNT_LOGGED_OUT = <<<'LI'
  <i title="Mi cuenta" class="far fa-user fa-fw fa-xl me-2"></i>Mi cuenta
LI;
  
  const MODULE_NAVBAR_ACCOUNT_LOGGED_IN = <<<'LI'
  <span class="position-relative">
    <i title="Mi cuenta" class="fas fa-user fa-fw fa-xl"></i>
    <span class="d-none d-sm-inline position-absolute top-0 start-100 translate-middle badge">
      <i class="fas fa-check fa-2xl text-info"></i>
    </span>
  </span>
  <span class="d-inline d-sm-none">%s, sesión iniciada</span>
LI;
  
  const MODULE_NAVBAR_ACCOUNT_LOGIN = 'Iniciar sesión';
  const MODULE_NAVBAR_ACCOUNT_LOGOFF = '%s, Cerrar sesión';
  const MODULE_NAVBAR_ACCOUNT = 'Mi cuenta';
  const MODULE_NAVBAR_ACCOUNT_HISTORY = 'Mis pedidos';
  const MODULE_NAVBAR_ACCOUNT_EDIT = 'Mis datos';
  const MODULE_NAVBAR_ACCOUNT_ADDRESS_BOOK = 'Direcciones';
  const MODULE_NAVBAR_ACCOUNT_PASSWORD = 'Contraseña';
  const MODULE_NAVBAR_ACCOUNT_REGISTER = 'Crear cuenta';
