import { HttpEvent, HttpHandlerFn, HttpInterceptorFn, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

export const authInterceptor: HttpInterceptorFn = (
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> => {
  const token = localStorage.getItem('am_token');
  if (token) {
    const authed = req.clone({ setHeaders: { Authorization: `Token ${token}` } });
    return next(authed);
  }
  return next(req);
};
