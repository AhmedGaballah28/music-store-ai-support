import logging
from typing import List, Dict, Any, Optional
from database import db_manager
import json
import re
import html

logger = logging.getLogger(__name__)


def sanitize_input(value: str, max_length: int = 500) -> str:
    """Sanitize user input to prevent SQL injection and other attacks"""
    if not value:
        return ""
    # Truncate to max length
    value = str(value)[:max_length]
    # Remove null bytes
    value = value.replace('\x00', '')
    # Basic sanitization - escape single quotes for SQL
    value = value.replace("'", "''")
    # Remove or escape potentially dangerous characters
    value = re.sub(r'[;\-\-]', '', value)
    return value.strip()


def validate_customer_id(customer_id: str) -> bool:
    """Validate that customer_id is a valid integer"""
    try:
        cid = int(customer_id)
        return 0 < cid < 1000000  # Reasonable range
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> bool:
    """Validate email format"""
    if not email or len(email) > 254:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

class MusicCatalogTools:
    """Tools for music catalog queries"""
    
    @staticmethod
    def get_albums_by_artist(artist: str) -> List[Dict]:
        """Retrieves albums by a given artist"""
        try:
            if not artist or len(artist) > 200:
                logger.warning("Invalid artist input")
                return []
            
            db = db_manager.get_database()
            
            # Sanitize input to prevent SQL injection
            artist_escaped = sanitize_input(artist)
            
            query = f"""
            SELECT DISTINCT 
                Album.AlbumId,
                Album.Title as AlbumTitle,
                Artist.Name as ArtistName
            FROM Album
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            WHERE LOWER(Artist.Name) LIKE LOWER('%{artist_escaped}%')
            ORDER BY Album.Title
            LIMIT 50
            """
            
            result = db.run(query)
            
            albums = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 3:
                                albums.append({
                                    'album_id': parts[0],
                                    'album_title': parts[1],
                                    'artist_name': parts[2]
                                })
                        except:
                            continue
            
            logger.info(f"Found {len(albums)} albums for artist '{artist}'")
            return albums
            
        except Exception as e:
            logger.error(f"Error getting albums by artist: {e}")
            return []
    
    @staticmethod
    def get_tracks_by_artist(artist: str) -> List[Dict]:
        """Retrieves tracks (songs) by a given artist or similar artists"""
        try:
            if not artist or len(artist) > 200:
                logger.warning("Invalid artist input")
                return []
            
            db = db_manager.get_database()
            artist_escaped = sanitize_input(artist)
            
            query = f"""
            SELECT DISTINCT
                Track.TrackId,
                Track.Name as TrackName,
                Album.Title as AlbumTitle,
                Artist.Name as ArtistName,
                Genre.Name as GenreName,
                Track.Milliseconds,
                Track.UnitPrice
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            LEFT JOIN Genre ON Track.GenreId = Genre.GenreId
            WHERE LOWER(Artist.Name) LIKE LOWER('%{artist_escaped}%')
            ORDER BY Track.Name
            LIMIT 20
            """
            
            result = db.run(query)
            
            tracks = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 7:
                                tracks.append({
                                    'track_id': parts[0],
                                    'track_name': parts[1],
                                    'album_title': parts[2],
                                    'artist_name': parts[3],
                                    'genre': parts[4] if parts[4] != 'None' else 'Unknown',
                                    'duration_ms': parts[5],
                                    'price': parts[6]
                                })
                        except:
                            continue
            
            logger.info(f"Found {len(tracks)} tracks for artist '{artist}'")
            return tracks
            
        except Exception as e:
            logger.error(f"Error getting tracks by artist: {e}")
            return []
    
    @staticmethod
    def get_songs_by_genre(genre: str) -> List[Dict]:
        """Fetches songs that match a specific genre"""
        try:
            if not genre or len(genre) > 100:
                logger.warning("Invalid genre input")
                return []
            
            db = db_manager.get_database()
            genre_escaped = sanitize_input(genre)
            
            query = f"""
            SELECT DISTINCT
                Track.TrackId,
                Track.Name as TrackName,
                Artist.Name as ArtistName,
                Album.Title as AlbumTitle,
                Genre.Name as GenreName
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            JOIN Genre ON Track.GenreId = Genre.GenreId
            WHERE LOWER(Genre.Name) LIKE LOWER('%{genre_escaped}%')
            ORDER BY RANDOM()
            LIMIT 10
            """
            
            result = db.run(query)
            
            songs = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 5:
                                songs.append({
                                    'track_id': parts[0],
                                    'track_name': parts[1],
                                    'artist_name': parts[2],
                                    'album_title': parts[3],
                                    'genre_name': parts[4]
                                })
                        except:
                            continue
            return songs
            
        except Exception as e:
            logger.error(f"Error getting songs by genre: {e}")
            return []
    
    @staticmethod
    def check_for_songs(song_title: str) -> List[Dict]:
        """Checks if a song exists by its name"""
        try:
            if not song_title or len(song_title) > 200:
                logger.warning("Invalid song title input")
                return []
            
            db = db_manager.get_database()
            song_escaped = sanitize_input(song_title)
            
            query = f"""
            SELECT 
                Track.TrackId,
                Track.Name as TrackName,
                Artist.Name as ArtistName,
                Album.Title as AlbumTitle,
                Track.UnitPrice
            FROM Track
            JOIN Album ON Track.AlbumId = Album.AlbumId
            JOIN Artist ON Album.ArtistId = Artist.ArtistId
            WHERE LOWER(Track.Name) LIKE LOWER('%{song_escaped}%')
            LIMIT 10
            """
            
            result = db.run(query)
            
            songs = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 5:
                                songs.append({
                                    'track_id': parts[0],
                                    'track_name': parts[1],
                                    'artist_name': parts[2],
                                    'album_title': parts[3],
                                    'price': parts[4]
                                })
                        except:
                            continue
            return songs
            
        except Exception as e:
            logger.error(f"Error checking for songs: {e}")
            return []


class InvoiceTools:
    """Tools for invoice and customer queries"""
    
    @staticmethod
    def get_invoices_by_customer_sorted_by_date(customer_id: str) -> List[Dict]:
        """Retrieves all invoices for a customer, sorted by invoice date (most recent first)"""
        try:
            if not validate_customer_id(customer_id):
                logger.warning(f"Invalid customer_id: {customer_id}")
                return []
            
            db = db_manager.get_database()
            # Use integer validation instead of string escaping
            safe_customer_id = int(customer_id)
            
            query = f"""
            SELECT 
                Invoice.InvoiceId,
                Invoice.InvoiceDate,
                Invoice.Total,
                Invoice.BillingCity,
                Invoice.BillingCountry
            FROM Invoice
            WHERE Invoice.CustomerId = {safe_customer_id}
            ORDER BY Invoice.InvoiceDate DESC
            LIMIT 100
            """
            
            result = db.run(query)
            
            invoices = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 5:
                                invoices.append({
                                    'invoice_id': parts[0],
                                    'invoice_date': parts[1],
                                    'total': parts[2],
                                    'billing_city': parts[3],
                                    'billing_country': parts[4]
                                })
                        except:
                            continue
            
            logger.info(f"Found {len(invoices)} invoices for customer {customer_id}")
            return invoices
            
        except Exception as e:
            logger.error(f"Error getting invoices by customer: {e}")
            return []
    
    @staticmethod
    def get_invoices_sorted_by_unit_price(customer_id: str) -> List[Dict]:
        """Retrieves all invoices for a customer, sorted by unit price (highest to lowest)"""
        try:
            if not validate_customer_id(customer_id):
                logger.warning(f"Invalid customer_id: {customer_id}")
                return []
            
            db = db_manager.get_database()
            safe_customer_id = int(customer_id)
            
            query = f"""
            SELECT DISTINCT
                Invoice.InvoiceId,
                Invoice.InvoiceDate,
                Invoice.Total,
                MAX(InvoiceLine.UnitPrice) as MaxUnitPrice
            FROM Invoice
            JOIN InvoiceLine ON Invoice.InvoiceId = InvoiceLine.InvoiceId
            WHERE Invoice.CustomerId = {safe_customer_id}
            GROUP BY Invoice.InvoiceId, Invoice.InvoiceDate, Invoice.Total
            ORDER BY MaxUnitPrice DESC
            LIMIT 100
            """
            
            result = db.run(query)
            
            invoices = []
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 4:
                                invoices.append({
                                    'invoice_id': parts[0],
                                    'invoice_date': parts[1],
                                    'total': parts[2],
                                    'max_unit_price': parts[3]
                                })
                        except:
                            continue
            return invoices
            
        except Exception as e:
            logger.error(f"Error getting invoices sorted by price: {e}")
            return []
    
    @staticmethod
    def get_employee_by_invoice_and_customer(invoice_id: str, customer_id: str) -> Dict:
        """Retrieves the employee information associated with a specific invoice and customer"""
        try:
            if not validate_customer_id(customer_id):
                logger.warning(f"Invalid customer_id: {customer_id}")
                return {}
            
            try:
                safe_invoice_id = int(invoice_id)
                if safe_invoice_id < 0 or safe_invoice_id > 1000000:
                    logger.warning(f"Invalid invoice_id: {invoice_id}")
                    return {}
            except (ValueError, TypeError):
                logger.warning(f"Invalid invoice_id format: {invoice_id}")
                return {}
            
            db = db_manager.get_database()
            safe_customer_id = int(customer_id)
            
            query = f"""
            SELECT 
                Employee.EmployeeId,
                Employee.FirstName,
                Employee.LastName,
                Employee.Title,
                Employee.Email,
                Employee.Phone
            FROM Customer
            JOIN Employee ON Customer.SupportRepId = Employee.EmployeeId
            JOIN Invoice ON Customer.CustomerId = Invoice.CustomerId
            WHERE Invoice.InvoiceId = {safe_invoice_id} AND Customer.CustomerId = {safe_customer_id}
            LIMIT 1
            """
            
            result = db.run(query)
            
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 6:
                                return {
                                    'employee_id': parts[0],
                                    'first_name': parts[1],
                                    'last_name': parts[2],
                                    'title': parts[3],
                                    'email': parts[4],
                                    'phone': parts[5]
                                }
                        except:
                            continue
            return {}
            
        except Exception as e:
            logger.error(f"Error getting employee info: {e}")
            return {}


class CustomerTools:
    """Tools for customer verification and lookup"""
    
    @staticmethod
    def get_customer_by_email(email: str) -> Optional[Dict]:
        """Get customer information by email"""
        try:
            if not validate_email(email):
                logger.warning(f"Invalid email format: {email}")
                return None
            
            db = db_manager.get_database()
            email_escaped = sanitize_input(email, max_length=254)
            
            query = f"""
            SELECT 
                CustomerId,
                FirstName,
                LastName,
                Email,
                Phone,
                City,
                Country
            FROM Customer
            WHERE LOWER(Email) = LOWER('{email_escaped}')
            LIMIT 1
            """
            
            result = db.run(query)
            
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 7:
                                return {
                                    'customer_id': parts[0],
                                    'first_name': parts[1],
                                    'last_name': parts[2],
                                    'email': parts[3],
                                    'phone': parts[4] if parts[4] != 'None' else None,
                                    'city': parts[5],
                                    'country': parts[6]
                                }
                        except:
                            continue
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by email: {e}")
            return None
    
    @staticmethod
    def get_customer_by_phone(phone: str) -> Optional[Dict]:
        """Get customer information by phone"""
        try:
            if not phone or len(phone) > 50:
                logger.warning("Invalid phone input")
                return None
            
            # Sanitize phone number - allow only digits, spaces, +, -, (), .
            sanitized_phone = re.sub(r'[^\d\s+\-().]', '', phone)
            if len(sanitized_phone) < 5:
                logger.warning(f"Phone number too short: {phone}")
                return None
            
            db = db_manager.get_database()
            phone_escaped = sanitized_phone.replace("'", "''")
            
            query = f"""
            SELECT 
                CustomerId,
                FirstName,
                LastName,
                Email,
                Phone,
                City,
                Country
            FROM Customer
            WHERE Phone = '{phone_escaped}'
            LIMIT 1
            """
            
            result = db.run(query)
            
            if result and isinstance(result, str) and '(' in result:
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 7:
                                customer_data = {
                                    'customer_id': parts[0],
                                    'first_name': parts[1],
                                    'last_name': parts[2],
                                    'email': parts[3],
                                    'phone': parts[4] if parts[4] != 'None' else None,
                                    'city': parts[5],
                                    'country': parts[6]
                                }
                                logger.info(f"Found customer by phone: {customer_data['customer_id']}")
                                return customer_data
                        except Exception as e:
                            logger.error(f"Error parsing customer data: {e}")
            
            phone_part = re.sub(r'[^\d]', '', phone)[-8:]
            phone_part_escaped = phone_part.replace("'", "''")
            
            query2 = f"""
            SELECT 
                CustomerId,
                FirstName,
                LastName,
                Email,
                Phone,
                City,
                Country
            FROM Customer
            WHERE Phone LIKE '%{phone_part_escaped}%'
            LIMIT 1
            """
            
            result2 = db.run(query2)
            
            if result2 and isinstance(result2, str) and '(' in result2:
                lines = result2.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 7:
                                return {
                                    'customer_id': parts[0],
                                    'first_name': parts[1],
                                    'last_name': parts[2],
                                    'email': parts[3],
                                    'phone': parts[4] if parts[4] != 'None' else None,
                                    'city': parts[5],
                                    'country': parts[6]
                                }
                        except:
                            continue
            
            logger.info(f"No customer found with phone: {phone}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by phone: {e}")
            return None
    
    @staticmethod
    def get_customer_by_id(customer_id: str) -> Optional[Dict]:
        """Get customer information by ID"""
        try:
            if not validate_customer_id(customer_id):
                logger.warning(f"Invalid customer_id: {customer_id}")
                return None
            
            db = db_manager.get_database()
            safe_customer_id = int(customer_id)
            
            query = f"""
            SELECT 
                CustomerId,
                FirstName,
                LastName,
                Email,
                Phone,
                City,
                Country
            FROM Customer
            WHERE CustomerId = {safe_customer_id}
            LIMIT 1
            """
            
            result = db.run(query)
            
            if result and isinstance(result, str):
                lines = result.strip().split('\n')
                for line in lines:
                    if '(' in line and ')' in line:
                        try:
                            data = line[line.find('(')+1:line.rfind(')')]
                            parts = [p.strip().strip("'") for p in data.split(',')]
                            if len(parts) >= 7:
                                return {
                                    'customer_id': parts[0],
                                    'first_name': parts[1],
                                    'last_name': parts[2],
                                    'email': parts[3],
                                    'phone': parts[4] if parts[4] != 'None' else None,
                                    'city': parts[5],
                                    'country': parts[6]
                                }
                        except:
                            continue
            return None
            
        except Exception as e:
            logger.error(f"Error getting customer by ID: {e}")
            return None