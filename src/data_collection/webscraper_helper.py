import json
import os
import dns.resolver
import whois
import socket
import random
import ssl
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit, urlunsplit
import geoip2.database
import geoip2.errors
import OpenSSL.crypto

def gather_and_save_dns_and_ip_info(domain, domain_folder):
    """Fetch and save DNS information for a given domain."""
    dns_records = {}
    record_types = ['A', 'NS', 'SOA', 'AAAA', 'CNAME', 'MX', 'TXT']

    resolver = dns.resolver.Resolver()
    resolver.timeout = 5
    resolver.lifetime = 15

    error_message = ""

    for record_type in record_types:
        try:
            answers = resolver.resolve(domain, record_type)
            dns_records[record_type] = [str(rdata) for rdata in answers]
        except dns.resolver.NoAnswer:
            dns_records[record_type] = "ERROR: No answer"
        except dns.resolver.NXDOMAIN:
            dns_records[record_type] = "ERROR: Domain does not exist"
        except dns.resolver.NoNameservers:
            dns_records[record_type] = "ERROR: No DNS servers found"
        except dns.resolver.LifetimeTimeout:
            dns_records[record_type] = "ERROR: DNS Lifetime Timeout"
            break
    
    # Fill in the remaining record types with "ERROR: DNS Lifetime Timeout"
    remaining_record_types = set(record_types) - set(dns_records.keys())
    for remaining_record_type in remaining_record_types:
        dns_records[remaining_record_type] = "ERROR: DNS Lifetime Timeout"

    if 'A' in dns_records and dns_records['A'] and isinstance(dns_records['A'], list):
        ip_address = random.choice(dns_records['A'])

        # Get AS_Number to the DNS records using GeoLite2-ASN.mmdb and geoip2
        try:
            with geoip2.database.Reader('GeoLite2-ASN.mmdb') as reader:
                response = reader.asn(ip_address)
                dns_records["AS_Number"] = response.autonomous_system_number
        except geoip2.errors.AddressNotFoundError:
            error_message += f"Address not found in the GeoIP database for IP Address {ip_address}."

    else:
        ip_address = None
        error_message += f"IP Address not found for: {domain}\n"
    
    filename = os.path.join(domain_folder, f"{domain}.dns.json")
    with open(filename, 'w') as file:
        json.dump(dns_records, file, indent=4)

    return ip_address, error_message

def gather_and_save_whois_info(domain, domain_folder):
    """Fetch and save WHOIS information for a given domain."""
    try:
        who_is_data = whois.whois(domain)
        filename = os.path.join(domain_folder, f"{domain}.whois.json")
        
        with open(filename, 'w') as file:
            json.dump(who_is_data, file, indent=4, default=str)
    except Exception as e:
        return f"Failed to fetch or save WHOIS information for {domain}. Error: {e}"

def gather_and_save_certificate_info_simple(domain, domain_folder, ip_address):
    """Fetch and save SSL certificate information for a domain."""
    cert_file_verified = os.path.join(domain_folder, f"{domain}.certificate-verified")
    cert_file_unverified = os.path.join(domain_folder, f"{domain}.certificate-unverified")
    base_url = ip_address

    exception = False
    error_message = ""
    error_flag = 0

    try:
        context = ssl.create_default_context()

        # Establish SSL connection with socket using port 443
        with socket.create_connection((ip_address, 443)) as sock:
            # Encrypted SSL connection for handshake 
            with context.wrap_socket(sock, server_hostname=domain) as ssl_sock:

                binary_cert = ssl_sock.getpeercert(binary_form=True)

                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, binary_cert)
                pem_cert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode('utf-8')

                with open(cert_file_verified, "w") as f:
                    f.write(pem_cert)

    except ssl.SSLError as e:
        exception = True
        error_message += f"Could not get SSL certificate for {base_url} with default context. Error: {e}. Trying no verify context.\n"
        error_flag = 1
    except socket.timeout:
        error_message +=  f"Socket operation timed out for {base_url} with default context. Will not try with no verify context."
        error_flag = 2
    except socket.error as e:
        exception = True
        error_message +=  f"Socket error for {base_url} with default context: {e}. Trying no verify context.\n"
        error_flag = 1

    # On a exception with default context, try again with CERT NONE verify mode
    if exception:
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            socket.setdefaulttimeout(10)

            # Establish SSL connection with socket using port 443
            with socket.create_connection((ip_address, 443)) as sock:
                # Encrypted SSL connection for handshake 
                with context.wrap_socket(sock) as ssl_sock:

                    binary_cert = ssl_sock.getpeercert(binary_form=True)

                    x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, binary_cert)
                    pem_cert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode('utf-8')

                    with open(cert_file_unverified, "w") as f:
                        f.write(pem_cert)

        except ssl.SSLError as e:
            error_message +=  f"Could not get SSL certificate for {base_url} with no verify context. Error: {e}"
            error_flag = 2
        except socket.timeout:
            error_message +=  f"Socket operation timed out for {base_url} with no verify context."
            error_flag = 2
        except socket.error as e:
            error_message +=  f"Socket error for {base_url} with no verify context: {e}"
            error_flag = 2

    return error_message, error_flag

def gather_and_save_html_content(browser, domain, domain_folder):
    """Fetch and save the HTML content of a domain."""
    html_content = browser.page_source
    
    # Save the fetched HTML content
    html_filename = os.path.join(domain_folder, f"{domain}.html")
    with open(html_filename, 'w', encoding="utf-8") as file:
        file.write(html_content)

def gather_and_save_final_url(browser, domain, domain_folder):
    """Save the final URL after all redirects."""
    final_url = browser.current_url
    filename = os.path.join(domain_folder, f"{domain}.final_url.txt")
    
    with open(filename, 'w') as file:
        file.write(final_url)

def gather_and_save_favicon(domain, domain_folder, final_url):
    """Fetch and save the favicon of a domain."""
    try:
        response = requests.get(final_url, timeout=10)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        soup = BeautifulSoup(response.text, 'html.parser')
        link = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')

        # If a favicon link is found in the HTML, use it. Otherwise, use the default favicon location
        if link and link.has_attr('href'):
            favicon_url = urljoin(final_url, link['href'])
        else:
            favicon_url = urljoin(final_url, 'favicon.ico')

        favicon = requests.get(favicon_url, timeout=10)
        favicon.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        filename = os.path.join(domain_folder, f"{domain}.favicon.ico")
        with open(filename, 'wb') as file:
            file.write(favicon.content)

    except requests.Timeout:
        return f"Request timed out for {domain}."
    except requests.HTTPError as http_err:
        return f"HTTP error occurred for {domain}: {http_err}"
    except requests.RequestException as err:
        return f"Error occurred for {domain}: {err}"

def save_load_time(load_time, domain, domain_folder):
    """Save the site load time."""
    filename = os.path.join(domain_folder, f"{domain}.loadtime.txt")
    with open(filename, 'w') as file:
        file.write(f"Load time for {domain}: {load_time:.2f} seconds\n")
